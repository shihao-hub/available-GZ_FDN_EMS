import tracemalloc
from typing import List, Dict

from lupa.luajit20 import LuaRuntime
from loguru import logger

from nicegui import ui, app

import settings

# todo: 这个不能默认开启吗？
tracemalloc.start()


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


async def create_common_header():
    # 暂且在此处执行一些通用操作，后续再移出去
    ui.query(".nicegui-content").classes("px-16")

    # just for test -> /docs/nicegui获取当前页面的标题.md
    @app.on_connect
    async def get_title():
        logger.debug("{}", await ui.run_javascript("return document.title;"))

    with ui.header().classes("items-center place-items-center"):
        # 标题
        with ui.link(target="/").classes("""
            row gap-4 items-center mr-auto
            no-underline text-lg text-white font-bold
        """):
            ui.html("""
            <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20.317 4.4921C18.7873 3.80147 17.147 3.29265 15.4319 3.00122C15.4007 2.9956 15.3695 3.00965 15.3534 3.03777C15.1424 3.40697 14.9087 3.88862 14.7451 4.26719C12.9004 3.99545 11.0652 3.99545 9.25832 4.26719C9.09465 3.8802 8.85248 3.40697 8.64057 3.03777C8.62449 3.01059 8.59328 2.99654 8.56205 3.00122C6.84791 3.29172 5.20756 3.80054 3.67693 4.4921C3.66368 4.49772 3.65233 4.5071 3.64479 4.51928C0.533392 9.09311 -0.31895 13.5545 0.0991801 17.9606C0.101072 17.9822 0.11337 18.0028 0.130398 18.0159C2.18321 19.4993 4.17171 20.3998 6.12328 20.9967C6.15451 21.0061 6.18761 20.9949 6.20748 20.9695C6.66913 20.3492 7.08064 19.6952 7.43348 19.0073C7.4543 18.967 7.43442 18.9192 7.39186 18.9033C6.73913 18.6597 6.1176 18.3626 5.51973 18.0253C5.47244 17.9981 5.46865 17.9316 5.51216 17.8997C5.63797 17.8069 5.76382 17.7104 5.88396 17.613C5.90569 17.5952 5.93598 17.5914 5.96153 17.6026C9.88928 19.3672 14.1415 19.3672 18.023 17.6026C18.0485 17.5905 18.0788 17.5942 18.1015 17.612C18.2216 17.7095 18.3475 17.8069 18.4742 17.8997C18.5177 17.9316 18.5149 17.9981 18.4676 18.0253C17.8697 18.3692 17.2482 18.6597 16.5945 18.9024C16.552 18.9183 16.533 18.967 16.5538 19.0073C16.9143 19.6942 17.3258 20.3483 17.7789 20.9686C17.7978 20.9949 17.8319 21.0061 17.8631 20.9967C19.8241 20.3998 21.8126 19.4993 23.8654 18.0159C23.8834 18.0028 23.8948 17.9831 23.8967 17.9616C24.3971 12.8676 23.0585 8.4428 20.3482 4.52021C20.3416 4.5071 20.3303 4.49772 20.317 4.4921ZM8.02002 15.2778C6.8375 15.2778 5.86313 14.2095 5.86313 12.8976C5.86313 11.5857 6.8186 10.5175 8.02002 10.5175C9.23087 10.5175 10.1958 11.5951 10.1769 12.8976C10.1769 14.2095 9.22141 15.2778 8.02002 15.2778ZM15.9947 15.2778C14.8123 15.2778 13.8379 14.2095 13.8379 12.8976C13.8379 11.5857 14.7933 10.5175 15.9947 10.5175C17.2056 10.5175 18.1705 11.5951 18.1516 12.8976C18.1516 14.2095 17.2056 15.2778 15.9947 15.2778Z"></path></svg>
            """).classes("fill-white scale-125 m-1")
            ui.label(settings.TITLE)

        # 选项卡
        with ui.row():
            for config in settings.TAB_CONFIGS:
                ui.link(config["name"], target=config["url"]).classes("no-underline text-lg text-white")

        # 设置
        with ui.link().classes("ml-auto mr-4 no-underline text-lg text-white"):
            # 【知识点】一门技术还得是官网，或者比官网更好的博客。比如：nicegui 官网被人按自己理解翻译整理的网站 https://visionz.readthedocs.io/zh-cn/latest/ext/nicegui/intro.html 就很好用，但是如果英语更好，显然**细细且反复**看官网即可。 # noqa
            # todo: 设置菜单
            with ui.icon("menu").classes("w-8 h-8 hover:bg-blue-400 hover:rounded-full"):
                with ui.menu() as menu:
                    def update_password():
                        """修改密码"""
                        if hasattr(update_password, "dialog"):
                            dialog: ui.dialog = getattr(update_password, "dialog")
                            dialog.open()
                            return

                        dialog: ui.dialog = ui.dialog()

                        def close_dialog():
                            """删除 dialog（因为 dialog.close 存在显示 bug）"""
                            dialog.delete()
                            delattr(update_password, "dialog")

                        with dialog.classes("w-64 h-64"):
                            with ui.card().classes("px-0 pt-0 rounded-none"):
                                with ui.row().classes("flex w-full justify-between items-center bg-gray-100 border"):
                                    ui.label("修改密码").classes("pl-4")
                                    # todo: props 如何使用？
                                    ui.button(icon="close", on_click=lambda: close_dialog()).classes("pr-4").props(
                                        "flat color=gray")
                                with ui.grid(columns=3).classes("items-center"):
                                    ui.label("旧密码").classes("justify-self-end")
                                    ui.input(placeholder="请输入密码", password=True, password_toggle_button=True)
                                    ui.space()

                                    ui.label("新密码").classes("justify-self-end")
                                    ui.input(placeholder="请输入密码", password=True, password_toggle_button=True)
                                    ui.space()

                                    ui.label("确认密码").classes("justify-self-end")
                                    ui.input(placeholder="请输入密码", password=True, password_toggle_button=True)
                                    ui.space()
                                with ui.element("div").classes("flex w-full justify-end"):
                                    with ui.row().classes("w-1/2"):
                                        def save():
                                            ui.notify("【未完成功能】修改密码保存成功！", type="positive")
                                            close_dialog()

                                        ui.button("关闭", on_click=lambda: close_dialog())
                                        ui.button("保存", on_click=lambda: save())

                        dialog.open()
                        setattr(update_password, "dialog", dialog)

                    def logout():
                        """用户注销，安全退出"""
                        # 暂且单纯跳转到 /login 页面
                        ui.navigate.to("/login")

                    ui.menu_item("修改密码", on_click=lambda: update_password(), auto_close=False)
                    ui.menu_item("退出登录", on_click=lambda: logout())

                    ui.separator()

                    admin_url = settings.BACKEND_BASE_URL + "/admin/"
                    ui.menu_item("后台管理", on_click=lambda: ui.navigate.to(admin_url))
