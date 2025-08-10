from loguru import logger

from nicegui import ui
from nicegui.elements.icon import Icon


@ui.page("/login", title="用户登录")
def page_login():
    ui.query(".nicegui-content").style("margin: 0; padding: 0; overflow: hidden;")

    # todo: 为什么 row 按顺序就可以做到这样？是行内 style 覆盖了继承自父容器的属性吗？
    with ui.row().classes("gap-0").style("height: 100vh; width: 100vw; position: relative;"):
        ui.column().style("height: 50%; width: 100%; background-color: #162332;")  # 上半部分，深蓝色
        ui.column().style("height: 50%; width: 100%; background-color: #e7e7e7;")  # 下半部分，浅灰色

        with ui.card().classes("px-10 pt-8 py-10 rounded-none") \
                .style("position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);"):
            with ui.row().classes("flex items-center m-auto"):
                Icon("account_box", size="50px", color="#444444")
                ui.label("登录").style("font-size: 28px; font-weight: normal; color: #333;")

            # todo: nicegui 除了 tailwind 还有强大的 quasar 框架，尤其它的 props
            user = ui.input("用户名").props("rounded-none outlined").style("width: 100%;")

            password = ui.input("密码", password=True, password_toggle_button=True) \
                .props("rounded-none outlined").style("width: 100%; margin-bottom: 10px;")

            with ui.row().style("width: 100%; justify-content: space-between;"):
                def login():
                    # ui.notify("【未完成功能】登录成功！", type="positive")
                    # todo: 调用后端 JWT 接口获得 token 并存储起来，存储到用户名下
                    # todo: 确定一下，假如这个存储越来越大怎么办？尤其 python 打包成一个 .exe 后，岂不是一直变大？
                    # todo: 是不是可以去学习一下 windows 的软件安装和分发？
                    ui.navigate.to("/")

                def register():
                    ui.notify("【未完成功能】注册成功！", type="positive")

                    logger.debug("{}, {}", user, password)

                ui.button("登录", icon="login", on_click=lambda: login()) \
                    .props("unelevated rounded-none") \
                    .style("background-color: #009688 !important; color: white; width: 45%; font-weight: bold;")

                ui.button("注册", icon="person_add", on_click=lambda: register()) \
                    .props("unelevated rounded-none") \
                    .style("background-color: #009688 !important; color: white; width: 45%; font-weight: bold;")
