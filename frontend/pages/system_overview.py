import math
import random
from typing import Optional

from nicegui import ui
from nicegui.element import Element
from watchfiles import awatch

import settings
import utils
import models

# 警告，特殊操作：此处为系统概览，需要依赖于其他 page 页的内容，为此我选择在此处导入其他 page 页信息
from .photovoltaic_bearing_capacity import create_plot_generation_consumption_curve_chart
from .multi_dimensional_evaluation import create_multi_dimensional_evaluation_radar_chart

# todo: 此处不够明了，根本没必要吧？或者能不能用什么注入的方式？直接在此处定义 page 的时候就将数据注入，似乎可以的
TAB_CONFIG = utils.locate_item(settings.TAB_CONFIGS, "id", "系统概览")


@ui.page(TAB_CONFIG["url"], title=TAB_CONFIG["title"], favicon=TAB_CONFIG["favicon"])
async def page():
    @ui.refreshable
    def top_statistic_cards():
        # fixme: 装饰器 @ui.refreshable 修饰的函数似乎无法为 async 函数
        data = utils.data_service.get_top_statistic_data()
        cards = [
            {"title": "安全性", "value": data["safety_score_0_100"], "icon": "security", "color": "red",
             "desc": "较昨日↑10.8%"},
            {"title": "经济性", "value": data["reliability_score_0_100"], "icon": "paid", "color": "green",
             "desc": "较昨日↑10.2%"},
            {"title": "可靠性", "value": data["economic_score_0_100"], "icon": "bolt", "color": "blue",
             "desc": "较昨日↑10.8%"},
            {"title": "环保性", "value": data["environment_score_0_100"], "icon": "eco", "color": "lime",
             "desc": "较昨日↑10.9%"},
        ]

        # 临时添加个 tag 用于标识变化
        # global selected_time_range 和 selected_freq 可以这样用，大概率是因为这里就是 js 的天生单线程
        for c in cards:
            c["title"] = f"{c["title"]} - {selected_data["time_range"]} - {selected_data["freq"]}"

        with ui.row().classes("w-full mb-6"):
            for c in cards:
                with ui.card().classes("flex-1 mx-2"):
                    ui.icon(c["icon"]).classes(f"text-3xl text-{c["color"]}-500")
                    ui.label(f"{c["value"]:.2f}").classes("text-2xl font-bold")
                    ui.label(c["title"]).classes("text-base text-gray-600")
                    ui.linear_progress(value=math.trunc(c["value"] / 100.0 * 100) / 100, color=c["color"]).classes(
                        "my-2")
                    ui.label(c["desc"]).classes("text-xs text-gray-400")

    def on_time_range_change(value):
        selected_data["time_range"] = value
        top_statistic_cards.refresh()

    def on_freq_change(value):
        selected_data["freq"] = value
        top_statistic_cards.refresh()

    # ------------------------------------------------------------------------ #

    await utils.create_common_header()

    # page 共享区（临时方案）
    selected_data = {
        "time_range": "今日",
        "freq": "15分钟",
    }

    # todo: 形成属于自己的使用 nicegui 的方式！最好能展示层和业务层耦合不要太严重。

    with ui.row().classes("w-full items-center justify-between mb-4"):
        # 左侧标题和副标题
        with ui.column():
            ui.label("柔性配电网络多维度评估系统").classes("text-xl font-bold text-gray-800")
            # ui.label("动态承载力分析 · 多维度评估 · 实时监控").classes("text-xs text-gray-500 mt-1")

        # todo: 修改全局按钮基础色

        # 右侧筛选和按钮
        with ui.row().classes("items-center"):
            async def select_plan(e):
                ui.notify(f"选择了 {e.value}")
                client_cache.so_plan = e.value
                await client_cache.save()

            client_cache, _ = await models.ClientCache.get_or_create(defaults=dict(client_id=ui.context.client.id))

            ui.label("选择方案").classes("text-sm text-gray-600 mr-1")
            ui.select(["方案一", "方案二", "方案三"],
                      value=client_cache.so_plan if client_cache.so_plan else "方案一",
                      on_change=select_plan).classes("mr-4 w-24")
            ui.label("时间范围").classes("text-sm text-gray-600 mr-1")
            ui.select(["今日", "本周", "本月"], value=selected_data["time_range"],
                      on_change=lambda e: on_time_range_change(e.value)).classes("mr-4 w-24")
            ui.label("数据频率").classes("text-sm text-gray-600 mr-1")
            ui.select(["15分钟", "1小时", "1天"], value=selected_data["freq"],
                      on_change=lambda e: on_freq_change(e.value)).classes("mr-4 w-24")
            ui.button("刷新数据", icon="refresh", on_click=lambda: top_statistic_cards.refresh()).classes(
                "bg-blue-500 text-white")

    # 顶部四个统计卡片
    top_statistic_cards()

    # todo: 实现放大和缩小不会错位，至少保证相对位置吧？
    # # 中间：左-折线图，右-雷达图
    # with ui.row().classes("w-full mb-6"):
    #     # 折线图
    #     with ui.card().classes("flex-[3] mr-4"):
    #         ui.label("光伏发电承载力分析").classes("font-bold mb-2")
    #         await create_plot_generation_consumption_curve_chart()
    #
    #     # 雷达图
    #     with ui.card().classes("flex-[2]"):
    #         ui.label("多维度评估指标").classes("font-bold mb-2")
    #         await create_multi_dimensional_evaluation_radar_chart()
    # 中间：左-折线图，右-雷达图（高度一致）
    with ui.row().classes("w-full flex mb-6 items-stretch"):  # 添加 items-stretch 使子元素等高
        # 折线图 - 添加 flex-col 和 h-full 确保内部填充
        with ui.card().classes("flex-[3] mr-4"):
            ui.label("光伏发电承载力分析").classes("font-bold mb-2")
            await create_plot_generation_consumption_curve_chart()

        # 雷达图 - 添加相同的布局类
        with ui.card().classes("flex-[2]"):
            ui.label("多维度评估指标").classes("font-bold mb-2")
            await create_multi_dimensional_evaluation_radar_chart()

    # 下方：条形图
    # fixme: 此处需要选项卡切换
    with ui.card().classes("w-full"):
        ui.label("详细指标得分").classes("font-bold mb-2")
        bar_labels = ["潮流不均衡度", "电压波动度", "电压越限率", "N-1通过率", "线路负载率"]
        bar_values = [random.randint(60, 100) for _ in bar_labels]
        ui.echart({
            "xAxis": {"type": "value", "max": 100},
            "yAxis": {"type": "category", "data": bar_labels},
            "series": [{
                "type": "bar",
                "data": bar_values,
                "label": {"show": True, "position": "right"}
            }],
            "tooltip": {},
        }).classes("w-full h-64")
