"""
翻译器模块
"""

from typing import Dict
from .translations import TRANSLATIONS


class Translator:
    """翻译器类"""

    def __init__(self, language: str = "zh_CN"):
        self.language = language

    def set_language(self, language: str):
        """设置语言"""
        if language in TRANSLATIONS:
            self.language = language

    def tr(self, key: str) -> str:
        """翻译文本"""
        try:
            return TRANSLATIONS[self.language][key]
        except KeyError:
            # 如果找不到翻译，返回中文或键名
            return TRANSLATIONS.get("zh_CN", {}).get(key, key)


# 全局翻译器实例
_translator = Translator("zh_CN")


def get_translator() -> Translator:
    """获取全局翻译器实例"""
    return _translator


def set_language(language: str):
    """设置全局语言"""
    _translator.set_language(language)
