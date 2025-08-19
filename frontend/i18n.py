from typing import Dict

# 仅作英转中操作，而且并不是英文翻译成中文，而是将英文字段转为中文

_dynamic_translations: Dict[str, str] = {}

_translations: Dict[str, str] = {
    "detail": "详情",
    "username": "用户名",
    "password": "密码",
}


def translate(text: str, default: str | None = None) -> str:
    """
    翻译文本为中文
    :param text: 要翻译的英文文本
    :param default: 如果没有找到翻译，返回的默认值（如果为 None 则返回原文本）
    :return: 翻译后的中文文本
    """
    # 先在动态翻译中查找
    if text in _dynamic_translations:
        return _dynamic_translations[text]

    # 然后在静态翻译中查找
    if text in _translations:
        return _translations[text]

    # 都没有找到，返回默认值或原文本
    return default if default is not None else text


def register_translation(english: str, chinese: str):
    """
    动态注册翻译项
    :param english: 英文相关文本
    :param english: 中文相关文本
    :return: None
    """
    _dynamic_translations[english] = chinese