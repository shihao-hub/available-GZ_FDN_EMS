import aiohttp
from loguru import logger

from nicegui import ui, app
from nicegui.elements.icon import Icon

import settings
import dialogs
import utils
import models


@ui.page("/login", title="用户登录")
def page_login():
    ui.query(".nicegui-content").style("margin: 0; padding: 0; overflow: hidden;")

    # SSO单点登录的实现流程：https://v.douyin.com/IN-Z_pSXKr0/（可以再次观看）

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
            username = ui.input("用户名").props("rounded-none outlined").style("width: 100%;")

            password = ui.input("密码", password=True, password_toggle_button=True) \
                .props("rounded-none outlined").style("width: 100%; margin-bottom: 10px;")

            with ui.row().style("width: 100%; justify-content: space-between;"):
                async def login():
                    # ui.notify("【未完成功能】登录成功！", type="positive")
                    # todo: 调用后端 JWT 接口获得 token 并存储起来，存储到用户名下
                    # todo: 确定一下，假如这个存储越来越大怎么办？尤其 python 打包成一个 .exe 后，岂不是一直变大？
                    # todo: 是不是可以去学习一下 windows 的软件安装和分发？

                    login_url = settings.BACKEND_BASE_URL + "/authentication/login/"

                    # todo: 【知识点】为了避免网络问题影响用户直观体验，在点击后，就应该出来加载动画给予用户反馈
                    async with aiohttp.ClientSession() as session:
                        async with session.post(login_url, json={
                            "username": username.value,
                            "password": password.value,
                        }) as response:
                            # todo: 确定一下响应是否会出现不为 json 格式的情况？（确实会...）
                            if response.status != 200:
                                ui.notify("账号不存在/账号错误/密码错误", type="negative")
                                # todo: 能否将 \n 也视为原始字符
                                logger.error(f"status: {response.status}, json: {await response.json()}")
                                return
                            # 登录成功，全局存储。此处有必要了解一下 nicegui 如何实现一个登录系统
                            # version 1.0: 通过客户端 id 作为全局存储 或者 存储在 cookie 中
                            #   - app.storage.user: 基于服务端存储，通过浏览器会话 cookie 中的唯一标识符关联用户。
                            #   - app.storage.browser：直接存储为浏览器会话 cookie，同用户的所有标签页共享。
                            ui.notify("登录成功！", type="positive")
                            resp_data = await response.json()
                            utils.auth_manager.store_access_token(resp_data["access"])
                            utils.auth_manager.store_refresh_token(resp_data["refresh"])
                            utils.auth_manager.store_user_info({"username": username.value})
                            await models.ClientCache.get_or_create(defaults={
                                "client_id": ui.context.client.id,
                                "username": username.value
                            })
                            # 延迟重定向至首页
                            ui.timer(0.5, lambda: ui.navigate.to("/"), once=True)

                async def register():
                    resgister_url = settings.BACKEND_BASE_URL + "/authentication/register/"
                    async with aiohttp.ClientSession() as session:
                        async with session.post(resgister_url, json={
                            "username": username.value,
                            "password": password.value,
                        }) as response:
                            if response.status != 200:
                                await dialogs.show_error_dialog(str(await response.json()))
                                return
                            logger.info("用户 {} 注册成功", await response.json())
                            ui.notify("注册成功！", type="positive")

                ui.button("登录", icon="login", on_click=lambda: login()) \
                    .props("unelevated rounded-none") \
                    .style("background-color: #009688 !important; color: white; width: 45%; font-weight: bold;")

                ui.button("注册", icon="person_add", on_click=lambda: register()) \
                    .props("unelevated rounded-none") \
                    .style("background-color: #009688 !important; color: white; width: 45%; font-weight: bold;")
