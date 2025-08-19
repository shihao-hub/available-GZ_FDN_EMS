import functools
import math
import pprint
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from nicegui import ui, app
from fastapi.responses import HTMLResponse

import settings
import utils
import echarts

TAB_CONFIG = utils.locate_item(settings.TAB_CONFIGS, "id", "潮流计算")

# pyecharts urls
LINE_LOADING_DETAILS_PANEL_URL = TAB_CONFIG["url"] + "/line_loading_details_panel.html"


@app.get(LINE_LOADING_DETAILS_PANEL_URL, response_class=HTMLResponse)
def line_loading_details_panel():
    if not hasattr(line_loading_details_panel, "html_str"):
        return ""
    return getattr(line_loading_details_panel, "html_str")


async def get_context_data():
    """获得 view 层的 context 数据，参考 django template 设计"""
    return {
        "line_details": await utils.data_service.get_line_loading_details(),
    }


@ui.page(TAB_CONFIG["url"], title=TAB_CONFIG["title"], favicon=TAB_CONFIG["favicon"])
async def page():
    await utils.create_common_header()

    context = await get_context_data()

    # 请求数据
    data = await utils.data_service.get_power_flow_calculation_result(onload=True)
    logger.debug(f"data: {data}")

    total_power = data["total_power"]
    max_loading = data["max_loading"]
    voltage_deviation = data["voltage_deviation"]
    network_loss = data["network_loss"]

    # skeleton - 指标卡
    with ui.row().classes("w-full mb-4"):
        for label, value in [
            ("总功率", f"{total_power:.2f} MW"),
            ("最大负载率", f"{max_loading:.4f} %"),  # todo: 这个数值太小了...
            ("电压偏差率", f"{voltage_deviation:.2f} %"),
            ("网损率", f"{network_loss:.2f} %")
        ]:
            with ui.card().classes("flex-1 text-center mx-2 shadow"):
                ui.label(label).classes("text-sm text-gray-600")
                ui.label(value).classes("text-2xl font-bold")

    # skeleton - 多曲线面积图
    # multi_curve_area_data
    times = data["times"]
    p_series = data["p_series"]
    q_series = data["q_series"]
    v_series = data["v_series"]
    power_range = data["power_range"]
    voltage_range = data["voltage_range"]

    with ui.card().classes("w-full"):
        ui.echart({
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["有功功率", "无功功率", "电压"]},
            "xAxis": {"type": "category", "data": times},
            "yAxis": [
                {"type": "value", "name": "功率(MW)", "min": power_range[0], "max": power_range[1]},
                {"type": "value", "name": "电压(pu)", "min": voltage_range[0], "max": voltage_range[1]}
            ],
            "series": [
                # todo: 弄明白这些属性的作用
                {"name": "有功功率", "type": "line", "data": p_series, "areaStyle": {}},
                {"name": "无功功率", "type": "line", "data": q_series, "areaStyle": {}},
                {"name": "电压", "type": "line", "yAxisIndex": 1, "data": v_series, "smooth": True}
            ]
        }).classes("w-full h-96 mt-4")

    # skeleton - 线路负载详情
    line_details = context["line_details"]

    # 【知识点】此处参考 js，将属性挂载在函数上！fixme: 但是需要注意多线程！当然如果是静态不变的数据那自然不需要担心。
    html_str, extra_data = echarts.render_line_loading_details(line_details)
    setattr(line_loading_details_panel, "html_str", html_str)

    with ui.card().classes("w-full min-h-64") as panel:
        # ui.label("线路负载详情").classes("text-base font-bold mt-2 mb-2")
        ui.html(f"""
                <iframe 
                    src="{LINE_LOADING_DETAILS_PANEL_URL}" 
                    style="width: 100%; height: 100%; border: none;"
                ></iframe>
            """).classes("w-full h-full").style(f"height: {int(extra_data["height"][:-2]) * 1.1}px;")
    return panel
