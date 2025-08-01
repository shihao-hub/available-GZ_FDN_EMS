# import importlib
# import settings # main.py 所在的目录是顶层包，home.py 是通过 main.py 执行的，所以 import settings 不会出错，但是 pycharm 找不到
# todo: 这是不对的！似乎是因为 pycharm 配置了 Enable Django Support？所以 pycharm 找不到 settings
#       我将 django 支持关闭后，给 backend 和 frontend 都 Mark Direcotory as Sources Root 后，似乎没问题了
# settings = importlib.import_module("settings")


def register_pages():
    from . import (
        home,
        multi_dimensional_evaluation,
        photovoltaic_bearing_capacity,
        power_flow_calculation,
        system_overview,
        topology_structure
    )
