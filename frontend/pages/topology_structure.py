import pprint
from pathlib import Path

import aiohttp
from loguru import logger
from nicegui import ui

import settings
import typeddicts
import utils

TAB_CONFIG = utils.locate_item(settings.TAB_CONFIGS, "id", "拓扑结构")

NODE_TYPE = {
    "变电站": {"symbol": "path://M0,0 L20,0 L20,20 L0,20 Z", "color": "#FF6E76", "borderColor": "#FF3D46"},
    "负载": {"symbol": "circle", "color": "#5470C6", "borderColor": "#2F4FAA"},
    "发电机": {"symbol": "diamond", "color": "#f68b2c"},
}

MIN_NODE_SIZE = 10
MAX_NODE_SIZE = 60
DEFAULT_NODE_SIZE = 30


@ui.page(TAB_CONFIG["url"], title=TAB_CONFIG["title"], favicon=TAB_CONFIG["favicon"])
async def page():
    def get_topology_chart_options(node_size=DEFAULT_NODE_SIZE):
        """生成电网拓扑图配置"""
        # todo: 仔细学习一下这个拓扑图配置，各个地方的配置！
        return {
            "title": {
                "text": "33节点配电网拓扑结构",
                "left": "center",
                "top": 10,
                "textStyle": {
                    "fontSize": 18,
                    "fontWeight": "bold",
                    "color": "#333"
                },
                "subtext": "基于功率流分析的可视化展示",
                "subtextStyle": {
                    "fontSize": 14,
                    "color": "#666"
                }
            },
            # todo: 处理一下
            "tooltip": {
                "trigger": "item",
                "formatter": """function(params){
                    if(params.dataType === "node"){
                        return `<div style="background:#fff;padding:10px;border-radius:4px;box-shadow:0 0 10px rgba(0,0,0,0.1)">
                            <b style="font-size:16px;color:#2c3e50">${params.data.name}</b>
                            <div style="margin-top:5px">
                                <span style="display:inline-block;width:70px">类型: </span> 
                                <span style="color:${params.data.itemStyle.color}">${params.data.type}</span>
                            </div>
                            <div>
                                <span style="display:inline-block;width:70px">功率: </span> 
                                <b>${params.data.power||0} kW</b>
                            </div>
                            <div>
                                <span style="display:inline-block;width:70px">节点ID: </span> 
                                ${params.data.id}
                            </div>
                        </div>`;
                    }
                    return "";
                }""",
                "backgroundColor": "rgba(255,255,255,0.95)",
                "borderWidth": 0,
                "padding": 0,
                "textStyle": {"color": "#333", "fontSize": 13}
            },
            "legend": {
                "data": list(NODE_TYPE.keys()),
                "top": 50,
                "right": 20,
                "orient": "vertical",
                "textStyle": {"fontSize": 12, "color": "#666"},
                "itemGap": 8,
                "itemWidth": 18,
                "itemHeight": 12
            },
            "animationDuration": 1500,
            "animationEasingUpdate": "quinticInOut",
            "series": [{
                "type": "graph",
                "layout": "force",
                "force": {
                    "repulsion": 200,  # 增加节点间斥力
                    "edgeLength": [80, 120],  # 调整边长度
                    "gravity": 0.05
                },
                "draggable": True,
                "symbolSize": node_size,
                "roam": True,
                "focusNodeAdjacency": True,
                "label": {
                    "show": True,
                    "position": "right",
                    "distance": 5,
                    "fontSize": 12,
                    "color": "#2c3e50",
                    "formatter": "{b}",
                    "backgroundColor": "rgba(255,255,255,0.7)",
                    "padding": [3, 5],
                    "borderRadius": 3
                },
                "edgeSymbol": ["none", "arrow"],
                "edgeSymbolSize": [8, 12],
                "edgeLabel": {
                    "show": False
                },
                "data": [
                    {
                        "id": str(n["id"]),
                        "name": n["name"],
                        "type": n["type"],
                        "category": n["type"],
                        "symbol": NODE_TYPE[n["type"]]["symbol"],
                        "symbolSize": node_size,
                        "itemStyle": {
                            "color": NODE_TYPE[n["type"]]["color"],
                            "borderColor": NODE_TYPE[n["type"]]["borderColor"],
                            "borderWidth": 2,
                            "shadowColor": "rgba(0,0,0,0.1)",
                            "shadowBlur": 5
                        },
                        "lineStyle": {
                            "color": "#aaa"
                        },
                        "power": n.get("power", None),
                        "label": {
                            "show": True
                        }
                    }
                    for n in nodes
                ],
                "categories": [
                    {"name": k, "symbol": v["symbol"], "itemStyle": {"color": v["color"]}}
                    for k, v in NODE_TYPE.items()
                ],
                # todo: 不要箭头
                "links": [
                    {
                        "source": str(e["source"]),
                        "target": str(e["target"]),
                        "lineStyle": {
                            "color": {
                                "type": "linear",
                                "x": 0, "y": 0, "x2": 1, "y2": 0,
                                "colorStops": [
                                    {"offset": 0, "color": "#5470C6"},
                                    {"offset": 1, "color": "#91CC75"}
                                ]
                            },
                            "width": 2.5,
                            "curveness": 0.1  # 轻微弯曲使线路更自然
                        }
                    }
                    for e in edges
                ],
                "lineStyle": {
                    "color": "#aaa",
                    "width": 2,
                    "opacity": 0.8
                },
                "emphasis": {
                    "focus": "adjacency",
                    "label": {
                        "show": True,
                        "fontWeight": "bold"
                    },
                    "lineStyle": {
                        "width": 4,
                        "color": "#FF6E76"
                    },
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0,0,0,0.3)"
                    }
                }
            }],
            # "backgroundColor": {
            #     "type": "linear",
            #     "x": 0, "y": 0, "x2": 0, "y2": 1,
            #     "colorStops": [
            #         {"offset": 0, "color": "#f8f9fa"},
            #         {"offset": 1, "color": "#e9ecef"}
            #     ]
            # }
        }

    @ui.refreshable
    def topology_chart(node_size=DEFAULT_NODE_SIZE):
        logger.debug("node_size: {}", node_size)
        with chart_container:
            options = get_topology_chart_options(node_size)
            ui.echart(options).classes("w-full h-screen h-[600px] min-h-[400px] bg-white")

    def update_topology_chart():
        # refresh 无效，不知道为什么，暂且选择 clear + rebuild 的方式实现
        chart_container.clear()
        topology_chart(node_size=node_size_slider.value)

        # .options 和 .update_options 属性均没有，因此暂时先选择 ui.refreshable
        # topology_chart.refresh(node_size_slider.value)

    # ------------------------------------ #

    await utils.create_common_header()

    data = await utils.data_service.get_topology_structure_data(onload=True)  # todo: 加载阶段，无数据，加载完成后，再获取数据？
    logger.debug("get_topology_structure: {}", data)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    # 控件区
    with ui.row().classes("items-center mb-4"):
        ui.label("节点大小")
        node_size_slider = ui.slider(min=MIN_NODE_SIZE, max=MAX_NODE_SIZE, value=DEFAULT_NODE_SIZE, step=1).classes(
            "w-64 ml-4")
        refresh_button = ui.button("刷新", icon="refresh", on_click=lambda: update_topology_chart()).classes("ml-4")

    chart_container = ui.card().classes("w-full h-screen")

    # 图表区
    topology_chart()

    # https://quasar.dev/vue-components/slider#lazy-input
    # - 实时更新（非惰性）：使用 @update:model-value 事件时，滑块值会随拖动实时更新数据模型。
    # - 惰性更新（Lazy Input）：使用 @change 事件时，数据模型只在拖拽结束时更新。
    node_size_slider.on("change", lambda e: update_topology_chart())
    refresh_button.on("click", lambda: update_topology_chart())
