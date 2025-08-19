import random
import uuid
from typing import Dict, Annotated

from loguru import logger

from nicegui import ui, app
from starlette.responses import HTMLResponse

import settings
import utils
import echarts

TAB_CONFIG = utils.locate_item(settings.TAB_CONFIGS, "id", "光伏承载力")


async def create_plot_generation_consumption_curve_chart(
        ref_ret: Annotated[Dict | None, "类 C 语言的指针风格补丁"] = None) -> ui.echart:
    generation_consumption_data = await utils.data_service.get_plot_generation_consumption_curve_data()
    hours = generation_consumption_data["hours"]
    gen = generation_consumption_data["gen"]
    use = generation_consumption_data["use"]

    if ref_ret is not None:
        ref_ret.update({"hours": hours})

    return ui.echart({
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["发电量", "消纳量"]},
        "xAxis": {"type": "category", "data": hours},
        "yAxis": {"type": "value", "name": "功率(MW)"},
        "series": [
            {"name": "发电量", "type": "line", "data": gen, "areaStyle": {}},
            {"name": "消纳量", "type": "line", "data": use, "areaStyle": {}}
        ]
    }).classes("w-full h-96")


@ui.page(TAB_CONFIG["url"], title=TAB_CONFIG["title"], favicon=TAB_CONFIG["favicon"])
async def page():
    await utils.create_common_header()

    context = {}

    # 顶部选择控件
    with ui.row().classes("items-center justify-between mb-4"):
        # todo: 数据来源 system_overview(那里是总览)
        ui.label("光伏发电承载力分析").classes("text-lg font-bold")
        with ui.row().classes("items-center"):
            # todo: 潮流计算也需要有
            ui.select(["方案一", "方案二", "方案三"], value="方案一", label="选择方案").classes("w-32 ml-2")
            ui.select(["晴天", "阴天", "多云"], value="晴天", label="天气条件").classes("w-32")
            ui.select(["春季", "夏季", "秋季", "冬季"], value="夏季", label="季节").classes("w-32 ml-2")
            ui.button("刷新数据", icon="refresh").classes("ml-2 bg-blue-500 text-white")

    # 发电量与消纳量曲线图
    await create_plot_generation_consumption_curve_chart(ref_ret=context)

    # 总览指标卡片
    overall_indicator_data = await utils.data_service.get_overall_indicator_data()
    with ui.row().classes("w-full mt-6"):
        for label, value, icon, delta in [
            ("总装机容量", f"{overall_indicator_data["installed_capacity_MW_approx"]:.2f} MW", "dns", 2.1),
            ("当前发电量", f"{overall_indicator_data["current_gen_avg_MW"]:.2f} MW", "flash_on", 5.2),
            ("实际消纳量", f"{overall_indicator_data["E_region_pv_consumed_MWh"]:.2f} MW", "power", 3.8),
            ("消纳效率", f"{overall_indicator_data["consume_rate_pct"]:.2f} %", "percent", 1.2)
        ]:
            with ui.card().classes("flex-1 text-center"):
                ui.icon(icon).classes("text-yellow-500 text-2xl")
                ui.label(label).classes("text-sm text-gray-500")
                ui.label(value).classes("text-2xl font-bold my-1")
                # fixme: 下面的两个组件内容需要动态生成，目前没有
                ui.label(f"+{delta:.1f}%").classes("text-green-500 text-xs")
                ui.linear_progress(value=delta / 10).classes("mt-1")

    # 区域容量分布

    # fixme: 属于当前客户端生成的路由，每次注册后，下次都需要删除掉。总之，后续要处理掉这个问题。

    url = TAB_CONFIG["url"] + f"/{uuid.uuid4()}/"
    logger.debug("[光伏承载力][光伏容量区域分布] url: {}", url)

    # todo: 目前还是静态数据
    html_str, _ = echarts.render_regional_capacity_distribution()

    @app.get(url, response_class=HTMLResponse)
    def register_route():
        return html_str

    # 获取第一个图表的宽度和高度（假设所有图表大小相同）
    # first_chart = page.charts[0]
    # width = first_chart.options["init_opts"].get("width", "100%")  # 默认为 "100%"
    # height = first_chart.options["init_opts"].get("height", "400px")  # 默认为 "400px"
    # print(f"图表宽度: {width}, 高度: {height}")

    with ui.card().classes("w-full h-full mt-6"):
        ui.label("光伏容量区域分布").classes("text-base font-bold mb-2")
        ui.html(f"""
                    <iframe 
                        src="{url}" 
                        style="width: 100%; height: 100%; border: none;"
                    ></iframe>
                """).classes("w-full h-full").style("height: 650px;")  # fixme: 不可使用绝对布局

    # 未来24小时预测图
    # todo: 待定
    with ui.card().classes("w-full mt-6"):
        ui.label("未来24小时预测").classes("text-base font-bold mb-2")
        forecast = [round(700 * max(0, 1 - abs(h - 12) / 12) + random.uniform(-30, 30), 1) for h in range(24)]
        ui.echart({
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": context["hours"]},
            "yAxis": {"type": "value", "name": "功率(kW)"},
            "series": [{
                "type": "line",
                "name": "发电预测",
                "data": forecast,
                "areaStyle": {"color": "#ffe58f"}
            }]
        }).classes("w-full h-80")
    return
