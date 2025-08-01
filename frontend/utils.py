from typing import List, Dict
from lupa.luajit20 import LuaRuntime


def locate_item(data: List[Dict], key, value) -> Dict:
    """从 List[Dict] 中定位到目标 Dict"""
    lua = getattr(locate_item, "lua")
    # fixme: 使用 lua.eval 是完全没有必要的，单纯练习罢了
    # todo: 找到 python 真的需要调用 lua 的场景！或者说实现出来一个类似 dst 的小型使用，python-引擎层，lua-业务层
    return lua.eval("""\
    function(data, key, value)
        for v in python.iter(data) do
            if v[key] == value then
                return v
            end
        end
        error("未找到对应元素，出错")
    end
    """)(data, key, value)


# 挂载，参考 js。说实在的，动态语言似乎就该这样！虽然可能导致维护困难，但是足够灵活，甚至可以改变自己的思维方式，增加思考维度和角度
setattr(locate_item, "lua", LuaRuntime())
