import warnings

import deprecation
from loguru import logger

from nicegui import ui, app

import settings
import pages
import utils
import models

# 【知识点】精确控制警告来源，仅显示 deprecation.DeprecatedWarning（加入其他第三方库也使用了 deprecation 库呢？）
warnings.filterwarnings("default", category=deprecation.DeprecatedWarning)

# todo: 数据显示是否正确，这是一定要核验的！

# 注册 pages
pages.register_pages()

# 挂载静态资源
app.add_static_files("/static", str(settings.SOURCE_DIR / "static"))

# 初始化数据库
models.tortoise_init()


# todo: 什么函数是在所有 ui 逻辑触发前执行的？且可以拿到 ui.context.client.id，依旧是 app.on_connect 吗？

@app.on_connect
async def verify_authorization_info():
    """在客户端连接后进行权限校验，排除 /login 页面"""

    # 测试一下，似乎不行
    # await models.ClientCache.get_or_create(defaults=dict(client_id=ui.context.client.id))

    logger.debug("ui.context.client.id: {}, type: {}", ui.context.client.id, type(ui.context.client.id))
    if ui.context.client.page.path.startswith("/login"):
        return
    await utils.verify_authorization_info()


# todo: 添加全局错误处理弹窗，只要是非受检异常，就弹这个窗口（如：原因：意料之外的错误，请联系维护人员。时间：X-X-X X:X:X）


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title=settings.TITLE,
           favicon=settings.FAVICON,
           host=settings.HOST,
           port=settings.PORT,
           reconnect_timeout=settings.RECONNECT_TIMEOUT,
           **settings.NATIVE_CONFIGS,
           reload=False,
           show=False,
           on_air=settings.ON_AIR_TOKEN,
           # todo: 确定一下这个 storage_secret 是如何生成的？随机？
           storage_secret=settings.STORAGE_SECRET)
