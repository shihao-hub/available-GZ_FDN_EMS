from typing import List, Tuple, Dict, Annotated

from loguru import logger

from pyecharts.charts import Bar, Liquid, Page
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode


def render_regional_capacity_distribution() -> Tuple[str, Dict]:
    def make_liquid_card(idx: int, name: str, capacity: float, power: float) -> Liquid:
        ratio = 0.0 if not capacity else max(0.0, power / capacity)
        color = palette[idx % len(palette)]

        # 中心文本只显示一次：xx.x%
        center_label = JsCode("function(p){return (p.value*100).toFixed(1)+'%';}")

        li = (
            Liquid(init_opts=opts.InitOpts(width="380px", height="300px", js_host="/static/echarts/"))
            .add(
                series_name=name,
                data=[min(ratio, 1.2)],  # 允许略超 100%
                is_outline_show=True,
                shape="circle",
                label_opts=opts.LabelOpts(
                    formatter=center_label,
                    font_size=22,
                    color="#ffffff",
                    position="inside"
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=name,
                    subtitle=f"装机：{capacity:.1f} MW｜当前：{power:.1f} MW｜负载：{ratio * 100:.1f}%",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=18, color="#111827"),
                    subtitle_textstyle_opts=opts.TextStyleOpts(font_size=12, color="#4b5563"),
                )
            )
        )
        li.set_colors([color])  # 区域专属颜色
        return li

    # ------------------------------------------------------------------------ #

    # ===== 数据（单位 MW）=====
    regions = [
        {"name": "区域A", "capacity": 120.5, "power": 97.3},
        {"name": "区域B", "capacity": 95.8, "power": 92.0},
        {"name": "区域C", "capacity": 150.2, "power": 123.8},
        {"name": "区域D", "capacity": 88.3, "power": 73.1},
        {"name": "区域E", "capacity": 135.7, "power": 122.1},
        {"name": "区域F", "capacity": 110.8, "power": 99.6},
    ]

    # ===== 配色（每个区域一个颜色，循环使用）=====
    palette = ["#3b82f6", "#f59e0b", "#10b981", "#a855f7", "#ef4444", "#06b6d4"]

    page = Page(layout=Page.SimplePageLayout, js_host="/static/echarts/")  # 自适应宫格布局，不会重叠
    for i, r in enumerate(regions):
        page.add(make_liquid_card(i, r["name"], r["capacity"], r["power"]))

    return page.render_embed(), {}


def render_line_loading_details(line_details: List) -> Tuple[str, Annotated[Dict, "额外需要返回的数据"]]:
    """渲染 线路负载详情 页面"""

    def get_bar() -> Bar:
        # doc: 此处的 Bar 初始化太占空间，且无法收起，为此我选择将其作为内部函数使用（Python 同 JS，upvalue 较为随意和自由）
        return (
            # todo: 此处的 width 为绝对布局，height 生成又不够准确，需要修改和完善
            Bar(init_opts=opts.InitOpts(width="1430px", height=f"{dynamic_height}px", js_host="/static/echarts/"))
            # 2) 先加 x 轴类目
            .add_xaxis(y_names)
            # 已占用（渐变）
            .add_yaxis(
                "负载率",
                v_load,
                stack="total",
                category_gap="40%",
                bar_width=18,
                label_opts=opts.LabelOpts(
                    position="right",
                    formatter=JsCode("function(p){return p.value.toFixed(1)+'%';}"),  # 3) 简单安全
                    font_size=12,
                ),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode(
                        "new echarts.graphic.LinearGradient(0,0,1,0,["
                        "{offset:0,color:'#4caf50'},{offset:0.5,color:'#ffeb3b'},{offset:1,color:'#f44336'}])"
                    ),
                    border_radius=[9, 0, 0, 9],
                ),
            )
            # 剩余（灰）
            .add_yaxis(
                "剩余",
                v_rest,
                stack="total",
                category_gap="40%",
                bar_width=18,
                label_opts=opts.LabelOpts(is_show=False),
                itemstyle_opts=opts.ItemStyleOpts(color="#e9ecef", border_radius=[0, 9, 9, 0]),
            )
            .reversal_axis()  # 横向
            .set_global_opts(
                title_opts=opts.TitleOpts(title="线路负载详情（热力进度条）"),
                legend_opts=opts.LegendOpts(is_show=False),
                xaxis_opts=opts.AxisOpts(max_=100, axislabel_opts=opts.LabelOpts(formatter="{value}%")),
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
            )
        )

    # ------------------------------------------------------------------------ #

    # 动态计算图表高度 (每行30px + 基础高度)
    base_height = 120
    dynamic_height = max(420, 800, base_height + len(line_details) * 50)

    # 构建数据
    lines = []
    for detail in line_details:
        lines.append({
            "raw_name": f"{detail["name"]}",
            "name": f"{detail["name"]}  节点{detail["from"]} → 节点{detail["to"]}",
            "load": detail["loading"],
            "power": 12.05,  # 暂且为固定值
            "current": 126.7,  # 暂且为固定值
        })

    y_names = [it["raw_name"] for it in lines][::-1]
    v_load = [round(it["load"], 1) for it in lines][::-1]
    v_rest = [round(100 - it["load"], 1) for it in lines][::-1]

    logger.debug("dynamic_height: {}", dynamic_height)

    bar = get_bar()

    # todo: 第二个参数是否可以提供类型注解呢，以及这种编程方式是否合适（这种编程方式指的是返回的第二个方式为 dict）
    return bar.render_embed(), {
        "height": bar.height
    }
