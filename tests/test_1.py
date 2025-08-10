from nicegui import ui


def open_custom_dialog():
    dialog = ui.dialog()

    # 自定义标题栏
    with dialog:
        with ui.row().classes('w-full bg-gray-200 p-2 items-center justify-between border-b border-gray-300'):
            ui.label('这是对话框的描述文本').classes('text-sm text-gray-700')
            ui.button(icon='close', on_click=dialog.close).props('flat color=gray')

        # 对话框主体内容
        with ui.column().classes('p-4'):
            ui.label('这是对话框的主要内容区域')
    dialog.open()


# 触发对话框的按钮
ui.button('打开对话框', on_click=open_custom_dialog)

ui.run()