from nicegui import ui

import settings
import utils


async def create_home_page():
    # todo: 单纯搞个大屏展示图吧
    with ui.card().classes("mx-auto"):
        for config in settings.TAB_CONFIGS:
            with ui.element("ul"):
                with ui.element("li"):
                    with ui.row():
                        ui.icon(name=config["icon"])
                        ui.link(config["name"], target=config["url"], new_tab=True)


@ui.page("/")
async def page():
    # 这个如果不注释掉，会出现添加两个 <style> 然后这两个 <style> 居然不是相互覆盖，总之结果标头出现了两个
    # 我推测，一直都是两个，只不过 ui.header 多次添加后，相互叠加了！
    # await utils.create_common_header()
    # todo: 先验证 token，无效则直接重定向到登录页面
    from .system_overview import page as system_overview_page
    return await system_overview_page()
