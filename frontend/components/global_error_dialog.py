from nicegui import ui


class GlobalErrorDialog(ui.dialog):
    """
    全局错误弹窗

    需求背景：
    可能方案：1. 表单形式的错误弹窗（type="form"） 2.
    注意事项：nicegui 的 dialog 中发生的错误似乎无法继续弹窗。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with self:
            pass
