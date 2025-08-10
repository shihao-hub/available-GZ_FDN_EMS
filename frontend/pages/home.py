from nicegui import ui

import settings
import utils
from .system_overview import page as system_overview_page


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
    await utils.create_common_header()
    return await system_overview_page()
