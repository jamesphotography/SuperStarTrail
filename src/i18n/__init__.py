"""
国际化(i18n)模块
支持简体中文和英文
"""

from .translator import Translator, get_translator, set_language

__all__ = ['Translator', 'get_translator', 'set_language']
