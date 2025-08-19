from nicegui import ui

# Warning: utils.py 依赖了当前文件（dialogs.py），此处是否还能依赖 utils.py 文件？或者说如何杜绝这种情况？

# ====== 各种弹窗函数（暂且是函数，未来再拓展） ====== #

async def show_unauthorized_dialog(onload=False) -> ui.dialog | None:
    """展示无权限弹窗"""
    # fixme: 临时解决方案，如果是加载阶段，则无权限弹窗不必展示
    if onload:
        return None
    dialog = (
        ui.dialog()
        .classes("flex items-center justify-center")  # 居中显示
        .props("persistent")  # 无法关闭
    )

    # 使用现代化卡片设计
    with dialog, ui.card().classes("""
            min-w-[320px] min-h-[200px] p-6 rounded-xl shadow-xl
            border border-blue-100
            flex flex-col justify-between
        """):
        # 顶部图标和标题
        with ui.row().classes("items-center justify-center gap-3 mb-4"):
            ui.icon("lock", size="2rem", color="red").classes("text-red-500")
            ui.label("无权限访问").classes("text-2xl font-bold text-red-600")

        # 提示信息
        ui.label("您需要登录才能访问此内容").classes("text-lg text-gray-700 text-center mb-6")

        # 底部按钮组
        with ui.row().classes("justify-between w-full mt-4"):
            ui.space()
            ui.button("前往登录",
                      on_click=lambda: (dialog.delete(), ui.navigate.to("/login")),
                      icon="login"
                      ).props("flat color=primary").classes("px-6 bg-blue-500 text-white shadow")

    # 显示对话框
    dialog.open()
    return dialog


async def show_error_dialog(message: str) -> ui.dialog:
    """展示错误信息弹窗"""
    # todo: 如果 message 是 json 格式，则将其内容按照动态表单的方式展示，全部一行，不允许换行，超出内容鼠标放上去显示。
    #       除此以外，进行可能的国际化处理，如：("username", "用户名"), ("password", "密码")

    dialog = ui.dialog()
    with dialog, ui.card().classes("min-w-64 min-h-64 p-4"):
        ui.label(message).classes("text-center text-red-400 text-2xl")
    dialog.open()
    # 【知识点】返回值是 ui.dialog 时，pycharm 会警告要求该方法 await，即使方法没有用 async 修饰（python 异步不如 js 设计的好啊）
    return dialog
