import os
import configparser
import sys
from pathlib import Path

import tortoise
from tortoise import Tortoise

SOURCE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SOURCE_DIR.parent
CONFIG_DIR = PROJECT_DIR / "conf"
DEMO_DATA_DIR = SOURCE_DIR / "demo_data"

# 【知识点】conf 目录配置读取，这过于强依赖文件结构，要么统一到一个文件中，要么使用环境变量？
config = configparser.ConfigParser()
config.read(CONFIG_DIR / "common.ini")

DEBUG = True

BACKEND_BASE_URL = f"http://localhost:{config.getint("dynamic_settings", "BACKEND_PORT")}"

TITLE = "贵州山区柔性配电网络多维度评估系统"
FAVICON = None
HOST = "localhost"
PORT = config.getint("dynamic_settings", "FRONTEND_PORT")  # 临时的，后续要改为动态
RECONNECT_TIMEOUT = 10

NATIVE_CONFIGS = {
    "native": False,
}

if NATIVE_CONFIGS["native"]:
    # 【知识点】native 即使为 False，window_size/fullscreen 设置后，native 依旧生效了
    NATIVE_CONFIGS.update({"window_size""": (1200, 800), "fullscreen": False, })

ON_AIR_TOKEN = None  # 只有预览作用，太卡了。而且不知道为什么，进入后台管理的时候，把我电脑可能是浏览器卡死了，当然更大概率是新电脑自带的系统原因。
STORAGE_SECRET = "NOSET"

# 选项卡的配置信息
TAB_CONFIGS = [
    {
        "id": "系统概览",  # id
        "name": "系统概览",  # 名称
        "title": "系统概览",  # 标题
        "url": "/system-overview",  # url
        "favicon": None,  # favicon 图标
        "icon": "home",  # icon 图标
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

# ------------------------------------ tortoise-orm ------------------------------------ #
TORTOISE_ORM = {
    "connections": {"default": "sqlite://db.sqlite3"},
    "apps": {
        "models": {
            "models": ["aerich.models", "models"],
            "default_connection": "default",
        },
    },
}
