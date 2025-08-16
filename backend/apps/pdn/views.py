# -*- coding: utf-8 -*-
"""
IEEE33 时序潮流 + 动态承载力 (HC) 曲线
- 骨架: case33bw.txt
- 负荷: 多元数据.xlsx (首表, 前33列)
- PV:   PV 目录下 7 站数据 (CSV/XLSX)，与负荷对齐为 15min
- HC:   每个时刻对统一倍率 alpha 做二分搜索, 得到 alpha*(t)

导出:
- metrics_timeseries.csv            KPI 时序
- distribution_curves.csv           主图曲线(总有功/Vmin/Vmax/HC_alpha)
- line_loading_timeseries.parquet   线路负载率时序（若缺引擎，则写 CSV 兜底）
- bus_voltage_timeseries.parquet    母线电压时序（若缺引擎，则写 CSV 兜底）
- line_ranking_latest.csv           某一时刻线路排行
- pv_random_mapping.json            本次随机接入映射
- hc_timeseries.csv                 动态承载力 α*(t) + 瓶颈
- hc_summary.json                   HC 汇总统计
"""
import re, os, io, json, zipfile, random, warnings
import pandas as pd
import numpy as np
import pandapower as pp
from pathlib import Path

# -----------------------------
# 全局配置
# -----------------------------
SBASE_MVA = 100.0  # ← 按常见 IEEE33 的系统基准
VBASE_KV = 12.66
FREQ = "15min"
VMIN, VMAX = 0.95, 1.05
LINE_LOADING_MAX = 100.0
RANDOM_SEED = 42
RUN_ONLY_ONE_DAY = True
RUN_DAY = "2023-01-01"

# HC 搜索参数
HC_ALPHA_HI = 3.0  # α 搜索上界
HC_TOL = 1e-3  # 终止阈值
HC_MAX_IT = 20  # 最大迭代


# -----------------------------
# 小工具：安全保存 parquet（没引擎就退回 CSV）
# -----------------------------
def _safe_to_parquet(df: pd.DataFrame, path_parquet: Path, fallback_csv: Path):
    try:
        df.to_parquet(path_parquet)
    except Exception as e:
        warnings.warn(f"to_parquet 失败（{e}），已改为写 CSV：{fallback_csv.name}")
        df.to_csv(fallback_csv, encoding="utf-8-sig")


# -----------------------------
# 1) 解析 case33bw（支路阻抗按 p.u. 读入）
# -----------------------------
def parse_case33bw(txt_path: Path):
    text = txt_path.read_text(encoding="utf-8", errors="ignore")

    def parse_matrix(name):
        pat = re.compile(rf"mpc\.{name}\s*=\s*\[(.*?)\];", re.S)
        m = pat.search(text)
        if not m: return None
        body = m.group(1).strip()
        rows = []
        for line in body.split(";"):
            line = line.strip()
            if not line: continue
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", line)
            if nums: rows.append([float(x) for x in nums])
        return pd.DataFrame(rows)

    bus = parse_matrix("bus")
    branch = parse_matrix("branch")

    bus.columns = ["bus_i", "type", "Pd_kw", "Qd_kvar", "Gs", "Bs", "area", "Vm", "Va", "baseKV", "zone", "Vmax",
                   "Vmin"]
    branch.columns = ["fbus", "tbus", "r_pu", "x_pu", "b", "rateA", "rateB", "rateC", "ratio", "angle", "status",
                      "angmin", "angmax"]
    branch = branch[branch["status"] == 1].copy()  # 只保留常开

    bus_df = bus[["bus_i", "baseKV"]].copy()
    bus_df.columns = ["bus_i", "base_kv"]

    # 注意：这里保留为 p.u. 名字，建网时再转欧姆
    line_df = branch[["fbus", "tbus", "r_pu", "x_pu"]].copy()
    line_df["length_km"] = 1.0
    line_df["c_nf_per_km"] = 0.0
    line_df["max_i_ka"] = 0.4
    return bus_df.reset_index(drop=True), line_df.reset_index(drop=True)


# -----------------------------
# 2) 建网（把 p.u. → 欧姆，再 create_line_from_parameters）
# -----------------------------
def build_net(bus_df, line_df, sbase=SBASE_MVA):
    net = pp.create_empty_network(sn_mva=sbase)

    bus_map = {}
    for _, r in bus_df.iterrows():
        b = int(r["bus_i"]);
        vn = float(r.get("base_kv", VBASE_KV))
        bus_map[b] = pp.create_bus(net, vn_kv=vn, name=f"Bus {b}")
    pp.create_ext_grid(net, bus=bus_map[1], vm_pu=1.0, name="Grid")

    # pu → ohm : Zbase = V^2 / S
    Zbase = (VBASE_KV ** 2) / SBASE_MVA  # Ohm
    for _, ln in line_df.iterrows():
        fb, tb = bus_map[int(ln["fbus"])], bus_map[int(ln["tbus"])]
        r_ohm = float(ln["r_pu"]) * Zbase
        x_ohm = float(ln["x_pu"]) * Zbase
        pp.create_line_from_parameters(
            net, fb, tb, length_km=float(ln["length_km"]),
            r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm, c_nf_per_km=float(ln["c_nf_per_km"]),
            max_i_ka=float(ln["max_i_ka"]), name=f"{int(ln['fbus'])}-{int(ln['tbus'])}"
        )
    return net, bus_map


# -----------------------------
# 3) 负荷 & PV 读取
# -----------------------------
def read_load_pu(xlsx_path: Path, freq=FREQ):
    df = pd.read_excel(xlsx_path, sheet_name=0)
    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    if df[time_col].isna().all():
        df[time_col] = pd.date_range("2024-01-01", periods=len(df), freq="H")
    df = df.set_index(time_col).sort_index()

    load = df[df.columns[:33]].copy()
    load.columns = list(range(1, 34))
    if load.index.inferred_freq != freq:
        load = load.resample(freq).interpolate()
    return load  # p.u.


def read_pv_pu(pv_rar_or_dir: Path, target_index, freq="15min"):
    """
    - 输入为目录：递归读取 csv/xlsx/xls，组装为 [time × 7]（PV1..PV7）
    - 输入为 rar：保持原逻辑
    - 会与 target_index 对齐为 15min
    - CSV/xlsx 第一列优先当时间；若不是时间，则自动生成小时级索引
    - 数值若明显是 kW（max>2），自动换算到 p.u.：kW→MW→/SBASE_MVA
    """

    def _read_any_table(p: Path) -> pd.DataFrame:
        if p.suffix.lower() == ".csv":
            d = pd.read_csv(p, low_memory=False)  # 减少 dtype 警告
        else:
            d = pd.read_excel(p, sheet_name=0)
        # 设时间索引
        try:
            idx = pd.to_datetime(d.iloc[:, 0], errors="coerce")
            if idx.isna().all():
                raise ValueError
            d = d.set_index(d.columns[0])
        except Exception:
            d.index = pd.date_range("2024-01-01", periods=len(d), freq="H")
        # 仅保留数值列
        d = d.select_dtypes(include=[np.number])
        return d

    def _to_pu(ser: pd.Series) -> pd.Series:
        m = float(np.nanmax(ser.values)) if len(ser) else 0.0
        if m > 2.0:
            return (ser / 1000.0) / SBASE_MVA
        else:
            return ser

    if pv_rar_or_dir.is_dir():
        files = [p for p in pv_rar_or_dir.rglob("*") if p.suffix.lower() in (".csv", ".xlsx", ".xls")]
        if len(files) < 7:
            raise RuntimeError(f"在 {pv_rar_or_dir} 下只找到 {len(files)} 个 PV 文件，需 ≥7 个")
        files = sorted(files)[:7]  # 只取前7个；可自行调整策略

        cols = []
        for i, f in enumerate(files, 1):
            d = _read_any_table(f)
            if d.empty:
                raise RuntimeError(f"{f.name} 没有可用数值列")
            s = d.iloc[:, 0].astype(float)  # 取第一列功率
            s = _to_pu(s)
            # 确保时间索引
            if not isinstance(s.index, pd.DatetimeIndex):
                s.index = pd.to_datetime(s.index, errors="coerce")
                if s.index.isna().any():
                    s.index = pd.date_range("2024-01-01", periods=len(s), freq="H")
            # 统一 15min
            if pd.infer_freq(s.index) != freq:
                s = s.resample(freq).interpolate()
            # 对齐到负荷时间轴
            s = s.reindex(target_index).interpolate()
            s.name = f"PV{i}"
            cols.append(s)

        pv = pd.concat(cols, axis=1)
        return pv  # [time × 7]

    else:
        # rar 分支（保留）
        try:
            import rarfile
            with rarfile.RarFile(pv_rar_or_dir) as rf:
                parts = []
                for m in rf.infolist():
                    if m.filename.lower().endswith((".csv", ".xlsx", ".xls")):
                        data = rf.read(m)
                        if m.filename.lower().endswith(".csv"):
                            d = pd.read_csv(io.BytesIO(data))
                        else:
                            d = pd.read_excel(io.BytesIO(data), sheet_name=0)
                        try:
                            idx = pd.to_datetime(d.iloc[:, 0], errors="coerce")
                            if idx.isna().all():
                                raise ValueError
                            d = d.set_index(d.columns[0])
                        except Exception:
                            d.index = pd.date_range("2024-01-01", periods=len(d), freq="H")
                        d = d.select_dtypes(include=[np.number])
                        if not d.empty:
                            parts.append(d)
                if not parts:
                    raise RuntimeError("RAR 中未找到有效 PV 表格")
                pv = pd.concat(parts, axis=1)
        except Exception:
            warnings.warn("无法直接解压 PV.rar，请手动解压到 data/PV/。")
            raise RuntimeError("PV 数据读取失败（RAR 分支）。")

        pv = pv.iloc[:, :7].copy()
        pv.columns = [f"PV{i}" for i in range(1, 8)]
        if pv.index.inferred_freq != freq:
            pv = pv.resample(freq).interpolate()
        pv = pv.reindex(target_index).interpolate()
        return pv


# -----------------------------
# 4) 注入 & 运行
# -----------------------------
def apply_injections(net, bus_map, p_load_pu_row: pd.Series,
                     pv_bus_map: dict, pv_pu_row: pd.Series, alpha: float = 1.0):
    # 重建元素（简单直观；若要极致提速可改为预创建后更新）
    if len(net.load): net.load.drop(net.load.index, inplace=True)
    if len(net.sgen): net.sgen.drop(net.sgen.index, inplace=True)

    PF = 0.95
    for bus_i, ppu in p_load_pu_row.items():
        p_mw = float(ppu) * net.sn_mva
        if p_mw <= 0: continue
        S = p_mw / PF
        q_mvar = max(0.0, (S ** 2 - p_mw ** 2) ** 0.5)
        pp.create_load(net, bus=bus_map[int(bus_i)], p_mw=p_mw, q_mvar=q_mvar)

    for pv_id, bus_i in pv_bus_map.items():
        base_pu = float(pv_pu_row.get(pv_id, 0.0))
        ppu = max(0.0, base_pu) * alpha
        p_mw = ppu * net.sn_mva
        if p_mw > 0:
            pp.create_sgen(net, bus=bus_map[int(bus_i)], p_mw=p_mw, q_mvar=0.0)


def runpf_and_check(net, vmin=VMIN, vmax=VMAX, line_max=LINE_LOADING_MAX):
    try:
        # 暂时关 numba，环境没装时更稳；装好 numba 后可去掉 numba=False
        pp.runpp(net, algorithm="bfsw", init="results", numba=False,
                 max_iteration=50, tolerance_mva=1e-5)
    except pp.LoadflowNotConverged:
        return False, "non_converge"

    vm = net.res_bus["vm_pu"].values
    if vm.min() < vmin - 1e-6 or vm.max() > vmax + 1e-6:
        return False, "voltage"
    if len(net.res_line) and net.res_line["loading_percent"].max() > line_max + 1e-3:
        return False, "line_loading"
    return True, "ok"


# -----------------------------
# 5) KPI 计算
# -----------------------------
def compute_kpis(net):
    p_grid = 0.0
    if hasattr(net, "res_ext_grid") and len(net.res_ext_grid):
        p_grid = float(-(net.res_ext_grid["p_mw"].sum()))
    max_loading = float(net.res_line["loading_percent"].max()) if len(net.res_line) else 0.0
    vm = net.res_bus["vm_pu"].values
    volt_dev_pct = float(np.max(np.abs(vm - 1.0)) * 100.0) if len(vm) else 0.0
    ploss = float(net.res_line["pl_mw"].sum()) if len(net.res_line) else 0.0
    total_load = float(net.load["p_mw"].sum()) if len(net.load) else 0.0
    loss_rate = (ploss / total_load * 100.0) if total_load > 1e-6 else 0.0
    return {
        "P_total_MW": p_grid,
        "max_loading_pct": max_loading,
        "voltage_dev_pct": volt_dev_pct,
        "loss_rate_pct": loss_rate
    }


# -----------------------------
# 6) HC（α）二分搜索（单时刻）
# -----------------------------
def search_alpha_once(net, bus_map, p_load_t, pv_map, pv_avail_t,
                      alpha_hi=HC_ALPHA_HI, tol=HC_TOL, max_it=HC_MAX_IT):
    lo, hi = 0.0, float(alpha_hi)
    best, reason = 0.0, "ok"
    for _ in range(max_it):
        a = 0.5 * (lo + hi)
        apply_injections(net, bus_map, p_load_t, pv_map, pv_avail_t, alpha=a)
        ok, why = runpf_and_check(net)
        if ok:
            best = a
            lo = a
        else:
            hi = a
            reason = why
        if hi - lo < tol:
            break
    return best, reason


# -----------------------------
# 7) 主流程
# -----------------------------
def main():
    random.seed(RANDOM_SEED)
    data_dir = Path("./data")

    # 骨架
    bus_df, line_df = parse_case33bw(data_dir / "case33bw.txt")
    net, bus_map = build_net(bus_df, line_df, sbase=SBASE_MVA)

    # 负荷 & PV（完整读入）
    load = read_load_pu(data_dir / "多元数据.xlsx", freq=FREQ)  # [t × 33] p.u.
    pv = read_pv_pu(data_dir / "PV", target_index=load.index)  # [t × 7] 0..1/p.u.

    # —— 只跑 2023-01-01 这一天（含起，不含次日）——
    if RUN_ONLY_ONE_DAY:
        DAY_START = pd.Timestamp(RUN_DAY + " 00:00:00")
        DAY_END = DAY_START + pd.Timedelta(days=1)
        mask = (load.index >= DAY_START) & (load.index < DAY_END)
        load = load.loc[mask]
        pv = pv.reindex(load.index).interpolate()
        if load.empty or pv.empty:
            raise RuntimeError(f"{RUN_DAY} 当天在数据中没有记录，请检查多元数据/PV的时间范围。")
        print("运行区间：", load.index.min(), "→", load.index.max(), "共", len(load), "步")

    # 防止 NaN 进入潮流
    load = load.fillna(0.0)
    pv = pv.fillna(0.0)

    # 随机接入（你可替换为固定方案表）
    pv_buses = random.sample(range(2, 34), 7)
    pv_map = {f"PV{i + 1}": pv_buses[i] for i in range(7)}
    pd.DataFrame([pv_map]).to_json(data_dir / "pv_random_mapping.json",
                                   force_ascii=False, orient="records", indent=2)

    # 容器
    kpi_rows = []
    line_loading_ts, bus_voltage_ts = {}, {}
    P_total, Vmin_kV, Vmax_kV, HC_alpha, HC_reason = [], [], [], [], []

    # 可选：首步自检
    t0 = load.index[0]
    apply_injections(net, bus_map, load.loc[t0], pv_map, pv.loc[t0], alpha=1.0)
    ok0, why0 = runpf_and_check(net)
    print("首步潮流：", ok0, why0, "vmin/vmax=",
          float(net.res_bus.vm_pu.min()), float(net.res_bus.vm_pu.max()))

    for i, t in enumerate(load.index, 1):
        p_load_t = load.loc[t]
        pv_t = pv.loc[t]

        # 1) α=1 的基线潮流
        apply_injections(net, bus_map, p_load_t, pv_map, pv_t, alpha=1.0)
        ok, _ = runpf_and_check(net)

        # KPI/曲线
        k = compute_kpis(net)
        k["time"] = t
        kpi_rows.append(k)
        P_total.append(k["P_total_MW"])
        Vmin_kV.append(float(net.res_bus["vm_pu"].min() * VBASE_KV))
        Vmax_kV.append(float(net.res_bus["vm_pu"].max() * VBASE_KV))

        # 时序结果
        line_loading_ts[t] = net.res_line["loading_percent"].round(2).to_dict()
        bus_voltage_ts[t] = net.res_bus["vm_pu"].round(4).to_dict()

        # 2) HC 二分搜索
        a_star, why = search_alpha_once(net, bus_map, p_load_t, pv_map, pv_t)
        HC_alpha.append(a_star)
        HC_reason.append(why)

        if i % 16 == 0:
            print(f"进度 {i}/{len(load.index)}  时刻: {t}, HC*={a_star:.3f}, 原因={why}")

    # ===== 导出 =====
    # KPI 时序
    metrics = pd.DataFrame(kpi_rows).set_index("time")
    metrics.to_csv(data_dir / "metrics_timeseries.csv", encoding="utf-8-sig")

    # 主图曲线（增加 HC_alpha）
    dist = pd.DataFrame({
        "P_total_MW": P_total,
        "Vmin_kV": Vmin_kV,
        "Vmax_kV": Vmax_kV,
        "HC_alpha": HC_alpha
    }, index=load.index)
    dist.to_csv(data_dir / "distribution_curves.csv", encoding="utf-8-sig")

    # HC 时序与汇总
    hc_df = pd.DataFrame({"alpha": HC_alpha, "bottleneck": HC_reason}, index=load.index)
    hc_df.to_csv(data_dir / "hc_timeseries.csv", encoding="utf-8-sig")

    hc_summary = {
        "alpha_mean": float(hc_df["alpha"].mean()),
        "alpha_p50": float(hc_df["alpha"].quantile(0.50)),
        "alpha_p90": float(hc_df["alpha"].quantile(0.90)),
        "alpha_min": float(hc_df["alpha"].min()),
        "alpha_max": float(hc_df["alpha"].max()),
        "bottleneck_counts": hc_df["bottleneck"].value_counts().to_dict()
    }
    Path(data_dir / "hc_summary.json").write_text(
        json.dumps(hc_summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 线路/母线时序（parquet 无引擎则写 CSV）
    _safe_to_parquet(pd.DataFrame(line_loading_ts).T,
                     data_dir / "line_loading_timeseries.parquet",
                     data_dir / "line_loading_timeseries.csv")
    _safe_to_parquet(pd.DataFrame(bus_voltage_ts).T,
                     data_dir / "bus_voltage_timeseries.parquet",
                     data_dir / "bus_voltage_timeseries.csv")

    # 某时刻排行（末时刻）
    last_line = pd.DataFrame(line_loading_ts[load.index[-1]].items(),
                             columns=["line", "loading_pct"]).sort_values("loading_pct", ascending=False)
    last_line.to_csv(data_dir / "line_ranking_latest.csv", index=False, encoding="utf-8-sig")

    print("✅ 输出文件：")
    for f in [
        "metrics_timeseries.csv",
        "distribution_curves.csv",
        "hc_timeseries.csv",
        "hc_summary.json",
        "line_loading_timeseries.parquet",
        "bus_voltage_timeseries.parquet",
        "line_ranking_latest.csv",
        "pv_random_mapping.json",
    ]:
        print(" -", (data_dir / f).resolve())


if __name__ == "__main__":
    main()
