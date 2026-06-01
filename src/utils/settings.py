"""
设置管理模块

管理应用程序的偏好设置
"""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

APP_VERSION = "1.0.2"


class Settings:
    """设置管理类"""

    DEFAULT_SETTINGS = {
        # 常规设置
        "general": {
            "use_default_output_dir": True,
            "auto_save_preview": False,
            "language": "zh_CN",
            "recent_dirs": [],
        },
        # RAW 处理设置
        "raw": {
            "exposure_compensation": 0.0,
            "denoise": False,
            "colorspace": "sRGB",  # sRGB, Adobe RGB, ProPhoto RGB
        },
        # 彗星效果设置
        "comet": {
            "default_fade_factor": 0.97,  # 默认中等尾巴长度
            "default_alignment": False,
            "default_gap_fill": True,  # 默认启用间隙填充
        },
        # 间隙填充设置
        "gap_filling": {
            "method": "morphological",  # morphological, interpolation
            "gap_size": 3,  # 像素
        },
        # 预览设置
        "preview": {
            "max_size": 800,  # 预览最大尺寸
            "update_interval": 3,  # 每处理N张更新一次预览
            "percentile_low": 1.0,  # 亮度拉伸低百分位
            "percentile_high": 99.5,  # 亮度拉伸高百分位
        },
        # 输出设置
        "output": {
            "image_format": "TIFF",  # TIFF, PNG, JPEG
            "video_format": "MP4",  # MP4, MOV
            "video_fps": 25,
            "video_resolution": [3840, 2160],  # 4K
            "video_quality": "high",  # high, medium, low
            "auto_timelapse": False,
        },
    }

    def __init__(self):
        """初始化设置"""
        self.settings_dir = Path.home() / ".superstartrail"
        self.settings_file = self.settings_dir / "settings.json"
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """加载设置"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    saved_settings = json.load(f)
                # 合并默认设置和保存的设置
                settings = self._merge_settings(
                    deepcopy(self.DEFAULT_SETTINGS), saved_settings
                )
                return settings
            except Exception:
                # 如果加载失败，返回默认设置
                return deepcopy(self.DEFAULT_SETTINGS)
        return deepcopy(self.DEFAULT_SETTINGS)

    def _merge_settings(
        self, default: Dict[str, Any], saved: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并默认设置和保存的设置"""
        for key, value in saved.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    default[key] = self._merge_settings(default[key], value)
                else:
                    default[key] = value
        return default

    def save_settings(self) -> bool:
        """保存设置"""
        try:
            # 确保目录存在
            self.settings_dir.mkdir(parents=True, exist_ok=True)

            # 保存设置
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get(self, category: str, key: str, default: Any = None) -> Any:
        """获取设置值"""
        try:
            return self.settings.get(category, {}).get(key, default)
        except Exception:
            return default

    def set(self, category: str, key: str, value: Any):
        """设置值"""
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value

    def reset_to_defaults(self):
        """重置为默认设置"""
        self.settings = deepcopy(self.DEFAULT_SETTINGS)

    # 便捷方法
    def get_video_fps(self) -> int:
        """获取视频帧率"""
        return self.get("output", "video_fps", 25)

    def get_fade_factor(self) -> float:
        """获取默认衰减因子"""
        return self.get("comet", "default_fade_factor", 0.980)

    def get_default_alignment(self) -> bool:
        """获取默认对齐设置"""
        return self.get("comet", "default_alignment", False)

    def get_default_gap_fill(self) -> bool:
        """获取默认间隙填充设置"""
        return self.get("comet", "default_gap_fill", False)

    def get_exposure_compensation(self) -> float:
        """获取曝光补偿"""
        return self.get("raw", "exposure_compensation", 0.0)

    def get_language(self) -> str:
        """获取语言设置"""
        return self.get("general", "language", "zh_CN")

    def set_language(self, language: str):
        """设置语言"""
        self.set("general", "language", language)
        self.save_settings()

    def get_gap_fill_method(self) -> str:
        """获取间隙填充方法"""
        return self.get("gap_filling", "method", "morphological")

    def get_gap_size(self) -> int:
        """获取间隙大小"""
        return self.get("gap_filling", "gap_size", 3)

    def get_preview_max_size(self) -> int:
        """获取预览最大尺寸"""
        return self.get("preview", "max_size", 800)

    def get_preview_update_interval(self) -> int:
        """获取预览更新间隔"""
        return self.get("preview", "update_interval", 3)

    def get_preview_percentiles(self) -> tuple:
        """获取预览拉伸百分位数"""
        low = self.get("preview", "percentile_low", 1.0)
        high = self.get("preview", "percentile_high", 99.5)
        return (low, high)

    def get_recent_dirs(self) -> list:
        """获取最近使用的目录列表"""
        return self.get("general", "recent_dirs", [])

    def add_recent_dir(self, path: str) -> None:
        """添加最近使用的目录（最多保留10条，自动去重）"""
        recent = self.get_recent_dirs()
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self.set("general", "recent_dirs", recent[:10])
        self.save_settings()

    def get_video_resolution(self) -> tuple:
        """获取视频分辨率"""
        res = self.get("output", "video_resolution", [3840, 2160])
        return tuple(res)


# 全局设置实例
_settings_instance = None


def get_settings() -> Settings:
    """获取全局设置实例"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
