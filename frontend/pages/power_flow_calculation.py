from concurrent.futures import ThreadPoolExecutor

from loguru import logger

from nicegui import ui

import settings
import utils

TAB_CONFIG = utils.locate_item(settings.TAB_CONFIGS, "id", "潮流计算")

thread_pool = ThreadPoolExecutor(max_workers=10)

powerflow_data = {}


@ui.refreshable
def create_calculate_panel():
    # 请求数据
    global powerflow_data
    data = powerflow_data
    voltages = data.get("voltages", [])
    loading = data.get("loading", [])
    total_power = data.get("total_power", 0)  # -
    max_loading = data.get("max_loading", 0)  # -
    voltage_deviation = data.get("voltage_deviation", 0)  # -
    network_loss = data.get("network_loss", 0)  # -
    line_details = data.get("line_details", [])

    # 生成模拟时间序列（假设 24 小时），把总功率等值简单复制以模拟多时刻
    times = [f"{h}:00" for h in range(24)]
    p_series = [total_power * (0.8 + 0.2 * ((i % 5) / 5)) for i in range(24)]
    q_series = [0.1 * p for p in p_series]
    v_series = [1.0 - 0.01 * ((i % 5) / 5) for i in range(24)]

    # 指标卡
    with ui.row().classes("w-full mb-4"):
        for label, value in [
            ("总功率", f"{total_power} MW"),
            ("最大负载率", f"{max_loading} %"),
            ("电压偏差", f"{voltage_deviation} %"),
            ("网损率", f"{network_loss} %")
        ]:
            with ui.card().classes("flex-1 text-center mx-2 shadow"):
                ui.label(label).classes("text-sm text-gray-600")
                ui.label(value).classes("text-2xl font-bold")

    # 多曲线面积图
    ui.echart({
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["有功功率", "无功功率", "电压"]},
        "xAxis": {"type": "category", "data": times},
        "yAxis": [
            {"type": "value", "name": "功率(MW)"},
            {"type": "value", "name": "电压(pu)", "min": 0.9, "max": 1.1}
        ],
        "series": [
            {"name": "有功功率", "type": "line", "data": p_series, "areaStyle": {}},
            {"name": "无功功率", "type": "line", "data": q_series, "areaStyle": {}},
            {"name": "电压", "type": "line", "yAxisIndex": 1, "data": v_series, "smooth": True}
        ]
    }).classes("w-full h-96 mt-4")

    # 线路负载详情
    ui.label("线路负载详情").classes("text-base font-bold mt-6 mb-2")
    for line in line_details:
        with ui.row().classes("items-center justify-between mb-2"):
            ui.label(f"{line["name"]} ({line["from"]}→{line["to"]})").classes("w-1/4")
            ui.label(f"负载率: {line["loading"]} %").classes("w-1/4")
            ui.label(f"功率: {line["power"]} MW").classes("w-1/4")
            ui.label(f"电流: {line["current"]} A").classes("w-1/4")
            ui.linear_progress(value=line["loading"] / 100.0).classes("w-full mt-1")


def fetch_powerflow_data_and_refresh():
    global powerflow_data
    logger.info("开始获取潮流数据")
    powerflow_data = {"voltages": [], "loading": []}  # todo: fetch_powerflow_data
    create_calculate_panel.refresh()


@ui.page(TAB_CONFIG["url"], title=TAB_CONFIG["title"], favicon=TAB_CONFIG["favicon"])
async def page():
    await utils.create_common_header()

    # thread_pool.submit(fetch_powerflow_data_and_refresh)
    create_calculate_panel()
    # fixme: 临时解决刷新数据问题
    # todo: 确定 nicegui 的 ui.refreshable 的原理
    ui.timer(0.3, lambda: fetch_powerflow_data_and_refresh(), once=True)
