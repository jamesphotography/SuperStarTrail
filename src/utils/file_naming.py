"""
文件命名服务

提供统一的文件命名逻辑，避免代码重复
"""

from pathlib import Path
from typing import List
from core.stacking_engine import StackMode


class FileNamingService:
    """文件命名服务，提供统一的命名规则"""

    # 堆栈模式映射表
    STACK_MODE_NAMES = {
        StackMode.COMET: "Comet",
        StackMode.LIGHTEN: "Lighten",
        StackMode.AVERAGE: "Average",
        StackMode.DARKEN: "Darken",
    }

    # 彗星尾巴长度映射表
    TAIL_LENGTH_NAMES = {
        0.95: "ShortTail",
        0.96: "ShortTail",
        0.97: "MidTail",
        0.98: "LongTail",
        0.99: "LongTail",
    }

    # 白平衡映射表
    WHITE_BALANCE_NAMES = {
        "camera": "CameraWB",
        "daylight": "Daylight",
        "auto": "AutoWB",
    }

    @staticmethod
    def extract_file_range(file_paths: List[Path]) -> str:
        """
        从文件列表中提取文件名范围

        Args:
            file_paths: 文件路径列表

        Returns:
            文件范围字符串，如 "IMG_0001-0100" 或 "first-last"
        """
        if not file_paths:
            return "untitled"

        first_name = file_paths[0].stem
        last_name = file_paths[-1].stem

        try:
            # 尝试提取数字后缀（格式：prefix_number）
            first_parts = first_name.rsplit('_', 1)
            last_parts = last_name.rsplit('_', 1)

            if len(first_parts) == 2 and len(last_parts) == 2:
                prefix = first_parts[0]
                first_num = first_parts[1]
                last_num = last_parts[1]
                return f"{prefix}_{first_num}-{last_num}"
        except Exception:
            pass

        # 回退到完整文件名
        return f"{first_name}-{last_name}"

    @classmethod
    def generate_output_filename(
        cls,
        file_paths: List[Path],
        stack_mode: StackMode,
        white_balance: str = "camera",
        comet_fade_factor: float = None,
        enable_gap_filling: bool = False,
        file_extension: str = "tif"
    ) -> str:
        """
        生成输出文件名

        Args:
            file_paths: 输入文件路径列表
            stack_mode: 堆栈模式
            white_balance: 白平衡设置
            comet_fade_factor: 彗星衰减因子（仅彗星模式需要）
            enable_gap_filling: 是否启用间隙填充
            file_extension: 文件扩展名（默认 tif）

        Returns:
            输出文件名
        """
        # 文件范围
        range_str = cls.extract_file_range(file_paths)

        # 堆栈模式
        mode_name = cls.STACK_MODE_NAMES.get(stack_mode, "Unknown")

        # 彗星尾巴长度（仅彗星模式）
        tail_suffix = ""
        if stack_mode == StackMode.COMET and comet_fade_factor is not None:
            tail_name = cls.TAIL_LENGTH_NAMES.get(comet_fade_factor, "MidTail")
            tail_suffix = f"_{tail_name}"

        # 白平衡
        wb_name = cls.WHITE_BALANCE_NAMES.get(white_balance, "CameraWB")

        # 间隙填充标记
        gap_suffix = "_GapFilled" if enable_gap_filling else ""

        # 组合文件名
        filename = f"{range_str}_{mode_name}{tail_suffix}_{wb_name}{gap_suffix}.{file_extension}"

        return filename

    @classmethod
    def generate_timelapse_filename(
        cls,
        file_paths: List[Path],
        stack_mode: StackMode,
        white_balance: str = "camera",
        comet_fade_factor: float = None,
        fps: int = 25,
        file_extension: str = "mp4"
    ) -> str:
        """
        生成延时视频文件名

        Args:
            file_paths: 输入文件路径列表
            stack_mode: 堆栈模式
            white_balance: 白平衡设置
            comet_fade_factor: 彗星衰减因子
            fps: 视频帧率
            file_extension: 文件扩展名（默认 mp4）

        Returns:
            视频文件名
        """
        # 文件范围
        range_str = cls.extract_file_range(file_paths)

        # 堆栈模式
        mode_name = cls.STACK_MODE_NAMES.get(stack_mode, "Unknown")

        # 彗星尾巴长度
        tail_suffix = ""
        if stack_mode == StackMode.COMET and comet_fade_factor is not None:
            tail_name = cls.TAIL_LENGTH_NAMES.get(comet_fade_factor, "MidTail")
            tail_suffix = f"_{tail_name}"

        # 白平衡
        wb_name = cls.WHITE_BALANCE_NAMES.get(white_balance, "CameraWB")

        # 组合文件名
        filename = f"{range_str}_{mode_name}{tail_suffix}_{wb_name}_Timelapse_{fps}FPS.{file_extension}"

        return filename
