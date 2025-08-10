from nicegui import ui, app

from loguru import logger

import settings
import pages

# 注册 pages
pages.register_pages()

# 挂载静态资源
app.add_static_files("/static", str(settings.SOURCE_DIR / "static"))

if __name__ == '__main__':
    ui.run(title=settings.TITLE,
           favicon=settings.FAVICON,
           host=settings.HOST,
           port=settings.PORT,
           reconnect_timeout=settings.RECONNECT_TIMEOUT,
           native=settings.NATIVE,
           reload=False,
           show=False,
           on_air=settings.ON_AIR_TOKEN,
           storage_secret=settings.STORAGE_SECRET)
