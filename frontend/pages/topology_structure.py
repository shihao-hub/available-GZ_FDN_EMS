from loguru import logger

from nicegui import ui

import settings
import utils

TAB_CONFIG = utils.locate_item(settings.TAB_CONFIGS, "id", "拓扑结构")


@ui.page(TAB_CONFIG["url"], title=TAB_CONFIG["title"], favicon=TAB_CONFIG["favicon"])
async def page():
    await utils.create_common_header()

    logger.debug("call account_tree_panel")
    data = {"nodes": [], "edges": []}  # todo: fetch_topology_data
    logger.debug("data: {}", data)
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    NODE_TYPE = {
        "变电站": {"symbol": "rect", "color": "#3478f6"},
        "负载": {"symbol": "circle", "color": "#44b07b"},
        "发电机": {"symbol": "diamond", "color": "#f68b2c"},
    }

    def get_topology_option(layout="force", node_size=30):
        # 生成 ECharts 配置
        return {
            "title": {"text": "33节点配电网拓扑结构", "left": "center", "top": 20,
                      "textStyle": {"fontSize": 20}},
            "tooltip": {
                "trigger": "item",
                "formatter": """function(params){
                                    if(params.dataType === "node"){
                                        return `<b>${params.data.name}</b><br>类型: ${params.data.type}<br>功率: ${params.data.power||"--"}<br>节点ID: ${params.data.id}`;
                                    }
                                    return "";
                                }"""
            },
            "legend": [{
                "data": list(NODE_TYPE.keys()),
                "top": 40,
                "right": 40,
                "orient": "vertical",
                "textStyle": {"fontSize": 14}
            }],
            "series": [{
                "type": "graph",
                "layout": layout,
                "symbolSize": node_size,
                "roam": True,
                "label": {"show": True, "position": "right", "fontSize": 12},
                "edgeSymbol": ["none", "arrow"],
                "edgeSymbolSize": [4, 8],
                "data": [
                    {
                        "id": str(n["id"]),
                        "name": n["name"],
                        "type": n["type"],
                        "category": n["type"],
                        "symbol": NODE_TYPE[n["type"]]["symbol"],
                        "itemStyle": {"color": NODE_TYPE[n["type"]]["color"]},
                        "power": n.get("power", None)
                    }
                    for n in nodes
                ],
                "categories": [
                    {"name": k, "itemStyle": {"color": v["color"]}} for k, v in NODE_TYPE.items()
                ],
                "links": [
                    {"source": str(e["source"]), "target": str(e["target"])} for e in edges
                ],
                "lineStyle": {"color": "#aaa", "width": 2},
                "emphasis": {"focus": "adjacency", "lineStyle": {"width": 4}},
            }]
        }

    # 控件区
    with ui.row().classes("items-center mb-4"):
        layout_type = ui.select(["力导向布局", "环形布局"], value="力导向布局", label="布局类型").classes(
            "w-40")
        ui.label("节点大小")
        node_size = ui.slider(min=10, max=30, value=15, step=1).classes("w-64 ml-4")
        refresh_btn = ui.button("刷新", icon="refresh").classes("ml-4")

    # 图表区
    chart = ui.echart(get_topology_option("force", 15)).classes(
        "w-full h-[600px] min-h-[400px] bg-white rounded shadow")

    # 交互逻辑
    def update_chart():
        layout = "force" if layout_type.value == "力导向布局" else "circular"
        chart.options = get_topology_option(layout, node_size.value)

    layout_type.on("update:model-value", lambda e: update_chart())
    node_size.on("update:model-value", lambda e: update_chart())
    refresh_btn.on("click", lambda: update_chart())
