from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent

DEBUG = True

TITLE = "贵州山区柔性配电网络多维度评估系统"
FAVICON = None
HOST = "localhost"
PORT = 12001  # 临时的，后续要改为动态
RECONNECT_TIMEOUT = 10
NATIVE = False
ON_AIR_TOKEN = None
STORAGE_SECRET = None

# 选项卡的配置信息
TAB_CONFIGS = [
    {
        "id": "系统概览",
        "name": "系统概览",
        "title": "系统概览",
        "url": "/system-overview",
        "favicon": None,
        "icon": "home",  # todo: 修改默认值，home 只是暂时的
    },
    {
        "id": "拓扑结构",
        "name": "拓扑结构",
        "title": "拓扑结构",
        "url": "/topology-structure",
        "favicon": None,
        "icon": "home",
    },
    {
        "id": "潮流计算",
        "name": "潮流计算",
        "title": "潮流计算",
        "url": "/power-flow-calculation",
        "favicon": None,
        "icon": "home",
    },
    {
        "id": "光伏承载力",
        "name": "光伏承载力",
        "title": "光伏承载力",
        "url": "/photovoltaic-bearing-capacity",
        "favicon": None,
        "icon": "home",
    },
    {
        "id": "多维度评估",
        "name": "多维度评估",
        "title": "多维度评估",
        "url": "/multi-dimensional-evaluation",
        "favicon": None,
        "icon": "home",
    }
]
