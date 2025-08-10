import random

from loguru import logger

from nicegui import ui

import settings
import utils

TAB_CONFIG = utils.locate_item(settings.TAB_CONFIGS, "id", "光伏承载力")


@ui.page(TAB_CONFIG["url"], title=TAB_CONFIG["title"], favicon=TAB_CONFIG["favicon"])
async def page():
    await utils.create_common_header()

    # 顶部选择控件
    with ui.row().classes("items-center justify-between mb-4"):
        ui.label("光伏发电承载力分析").classes("text-lg font-bold")
        with ui.row().classes("items-center"):
            ui.select(["晴天", "阴天", "多云"], value="晴天", label="天气条件").classes("w-32")
            ui.select(["春季", "夏季", "秋季", "冬季"], value="夏季", label="季节").classes("w-32 ml-2")
            ui.button("刷新数据", icon="refresh").classes("ml-2 bg-blue-500 text-white")

    # 发电量与消纳量曲线图
    hours = [f"{h}:00" for h in range(24)]
    gen = [round(random.uniform(0, 300) * max(0, 1 - abs(h - 12) / 12), 1) for h in range(24)]
    use = [round(g * random.uniform(0.8, 0.95), 1) for g in gen]
    ui.echart({
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["发电量", "消纳量"]},
        "xAxis": {"type": "category", "data": hours},
        "yAxis": {"type": "value", "name": "功率(MW)"},
        "series": [
            {"name": "发电量", "type": "line", "data": gen, "areaStyle": {}},
            {"name": "消纳量", "type": "line", "data": use, "areaStyle": {}}
        ]
    }).classes("w-full h-96")

    # 总览指标卡片
    with ui.row().classes("w-full mt-6"):
        for label, value, icon, delta in [
            ("总装机容量", "850.5 MW", "dns", 2.1),
            ("当前发电量", "625.3 MW", "flash_on", 5.2),
            ("实际消纳量", "598.7 MW", "power", 3.8),
            ("消纳效率", "95.7%", "percent", 1.2)
        ]:
            with ui.card().classes("flex-1 text-center"):
                ui.icon(icon).classes("text-yellow-500 text-2xl")
                ui.label(label).classes("text-sm text-gray-500")
                ui.label(value).classes("text-2xl font-bold my-1")
                ui.label(f"+{delta:.1f}%").classes("text-green-500 text-xs")
                ui.linear_progress(value=delta / 10).classes("mt-1")

    # 区域容量分布
    with ui.label("光伏容量区域分布").classes("text-base font-bold mt-8"):
        pass
    with ui.row().classes("w-full flex-wrap"):
        for name in ["区域A", "区域B", "区域C", "区域D", "区域E", "区域F"]:
            cap = round(random.uniform(80, 150), 1)
            cur = round(cap * random.uniform(0.7, 0.95), 1)
            rate = round(cur / cap * 100, 1)
            status = "正常" if rate <= 90 else "高负载"
            tag_color = "green" if rate <= 90 else "red"
            with ui.card().classes("w-1/3 p-4 m-2"):
                ui.label(name).classes("text-base font-bold")
                ui.label(f"装机容量: {cap} MW").classes("text-sm")
                ui.label(f"当前发电: {cur} MW").classes("text-sm")
                ui.label(f"负载率: {rate}%").classes("text-sm")
                ui.linear_progress(value=rate / 100, color="yellow").classes("mt-2")
                ui.label(status).classes(f"text-xs text-{tag_color}-500")

    # 未来24小时预测图
    with ui.card().classes("w-full mt-6"):
        ui.label("未来24小时预测").classes("text-base font-bold mb-2")
        forecast = [round(700 * max(0, 1 - abs(h - 12) / 12) + random.uniform(-30, 30), 1) for h in range(24)]
        ui.echart({
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": hours},
            "yAxis": {"type": "value", "name": "功率(kW)"},
            "series": [{
                "type": "line",
                "name": "发电预测",
                "data": forecast,
                "areaStyle": {"color": "#ffe58f"}
            }]
        }).classes("w-full h-80")
    return
