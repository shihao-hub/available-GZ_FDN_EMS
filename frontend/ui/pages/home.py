from nicegui import ui

import settings


@ui.page("/")
async def page():
    with ui.card().classes("mx-auto"):
        for config in settings.TAB_CONFIGS:
            with ui.element("ul"):
                with ui.element("li"):
                    with ui.row():
                        ui.icon(name=config["icon"])
                        ui.link(config["name"], target=config["url"], new_tab=True)
