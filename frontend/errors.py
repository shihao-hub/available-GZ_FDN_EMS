class AiErrorReportGenerator:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    async def ask_ai(self, error: str):
        """将错误信息传给 ai，并等待其响应"""
        prompt = f"""
        我在 python 编程的过程中，遇到了如下错误，请给我提供解决思路和方案。
        
        错误信息：
        {error}
        """
        # todo: 调用通义，并生成链接且返回
