from pathlib import Path

import pandas as pd
import pandapower as pp

from django.conf import settings
from rest_framework import views, generics, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

DEMO_DATA_PATH = settings.BASE_DIR / "apps" / "pdn" / "demo_data"


class PowerFlowCalculationRetrieveView(views.APIView):
    def _run_powerflow(self, load_scale=0.001, r_scale=1.0):
        # 加载数据
        bus_df = pd.read_csv(DEMO_DATA_PATH / "bus.csv")
        line_df = pd.read_csv(DEMO_DATA_PATH / "line.csv")

        net = pp.create_empty_network()

        # -----------------------
        # 添加母线，bus_i -1
        # -----------------------
        for _, row in bus_df.iterrows():
            pp.create_bus(
                net,
                vn_kv=row["baseKV"],
                name=f"Bus{int(row["bus_i"])}",
                index=int(row["bus_i"]) - 1
            )

        # -----------------------
        # 添加平衡节点
        # -----------------------
        slack_bus = int(bus_df[bus_df["type"] == 3]["bus_i"].values[0]) - 1
        pp.create_ext_grid(net, bus=slack_bus, vm_pu=1.0, name="Slack")

        # -----------------------
        # 添加负荷
        # -----------------------
        for _, row in bus_df.iterrows():
            if row["type"] != 3:
                pp.create_load(
                    net,
                    bus=int(row["bus_i"]) - 1,
                    p_mw=row["Pd"] / 1000 * load_scale,
                    q_mvar=row["Qd"] / 1000 * load_scale
                )

        # -----------------------
        # 添加线路，fbus/tbus -1
        # -----------------------
        for _, row in line_df.iterrows():
            pp.create_line_from_parameters(
                net,
                from_bus=int(row["fbus"]) - 1,
                to_bus=int(row["tbus"]) - 1,
                length_km=1,
                r_ohm_per_km=row["r"] * r_scale,
                x_ohm_per_km=row["x"] * r_scale,
                c_nf_per_km=0,
                max_i_ka=0.5
            )

        # -----------------------
        # 潮流计算
        # -----------------------
        try:
            pp.runpp(net, max_iteration=50)
            converged = True
        except Exception as e:
            return {"converged": False, "error": str(e)}

        # -----------------------
        # 返回数据
        # -----------------------
        return {
            "voltages": net.res_bus.vm_pu.round(4).tolist(),
            "loading": net.res_line.loading_percent.round(2).tolist(),
            "total_power": round(net.res_load.p_mw.sum(), 2),
            "max_loading": round(net.res_line.loading_percent.max(), 2),
            "voltage_deviation": round((1 - net.res_bus.vm_pu.min()) * 100, 2),
            "network_loss": round(net.res_line.pl_mw.sum() / net.res_load.p_mw.sum() * 100, 2)
            if net.res_load.p_mw.sum() != 0 else 0,
            "line_details": [
                {
                    "name": f"线{i + 1}",
                    "from": int(line_df.iloc[i]["fbus"]),
                    "to": int(line_df.iloc[i]["tbus"]),
                    "loading": round(net.res_line.loading_percent[i], 2),
                    "power": round(net.res_line.p_from_mw[i], 2),
                    "current": round(net.res_line.i_from_ka[i] * 1000, 2)
                }
                for i in range(len(net.res_line))
            ],
            "converged": converged
        }

    def get(self, request: Request):
        data = self._run_powerflow()
        return Response(data=data)


class TopologyStructureRetrieveView(views.APIView):
    """
    获取结构信息

    RESTful 风格命名：Retrieve 强调检索功能，Detail 适合返回详细拓扑，List 返回的是拓扑列表
    """

    def _load_network_data(self):
        bus_df = pd.read_csv(DEMO_DATA_PATH / "bus.csv")
        line_df = pd.read_csv(DEMO_DATA_PATH / "line.csv")
        return bus_df, line_df

    def get(self, request: Request):
        bus_df, line_df = self._load_network_data()

        # 构造节点
        nodes = []
        for _, row in bus_df.iterrows():
            # 不同 type 代表不同节点
            if row["type"] == 3:
                btype = "变电站"
            elif row["type"] == 2:
                btype = "发电机"
            else:
                btype = "负载"

            # node 数据结构，为了灵活，单纯 dict
            nodes.append({
                "id": int(row["bus_i"]),
                "name": f"Bus{int(row["bus_i"])}",
                "type": btype,
                "power": round(row.get("Pd", 0), 2)
            })

        # 构造边
        edges = []
        for _, row in line_df.iterrows():
            edges.append({
                "source": int(row["fbus"]),
                "target": int(row["tbus"])
            })

        return Response(data={"nodes": nodes, "edges": edges})
