"""
RAW 图像处理模块

负责读取和处理各种相机的 RAW 格式文件
"""

from typing import Optional, Dict, Any
from pathlib import Path
import numpy as np
import rawpy
from PIL import Image


class RawProcessor:
    """RAW 文件处理器 - 支持 RAW、TIFF、JPG 格式"""

    # 支持的 RAW 格式
    SUPPORTED_RAW_FORMATS = {".nef", ".cr2", ".arw", ".raf", ".dng", ".orf", ".rw2"}

    # 支持的其他格式
    SUPPORTED_IMAGE_FORMATS = {".tif", ".tiff", ".jpg", ".jpeg", ".png"}

    # 所有支持的格式
    SUPPORTED_FORMATS = SUPPORTED_RAW_FORMATS | SUPPORTED_IMAGE_FORMATS

    def __init__(self):
        """初始化处理器"""
        self.default_params = {
            "use_camera_wb": True,  # 使用相机白平衡
            "output_bps": 16,  # 16-bit 输出
            "output_color": rawpy.ColorSpace.sRGB,  # sRGB 色彩空间
            "gamma": (1, 1),  # 线性 gamma（不应用曲线）
            "no_auto_bright": True,  # 禁用自动亮度
            "exp_shift": 1.0,  # 曝光补偿（1.0 = 无补偿）
        }

    @staticmethod
    def is_supported_file(file_path: Path) -> bool:
        """
        检查文件是否为支持的格式

        Args:
            file_path: 文件路径

        Returns:
            如果是支持的格式返回 True
        """
        return file_path.suffix.lower() in RawProcessor.SUPPORTED_FORMATS

    @staticmethod
    def is_raw_file(file_path: Path) -> bool:
        """
        检查文件是否为 RAW 格式（保持向后兼容）

        Args:
            file_path: 文件路径

        Returns:
            如果是支持的格式返回 True
        """
        return file_path.suffix.lower() in RawProcessor.SUPPORTED_FORMATS

    def process(
        self,
        raw_path: Path,
        white_balance: str = "camera",
        exposure_compensation: float = 0.0,
        **kwargs,
    ) -> np.ndarray:
        """
        处理图像文件并返回 RGB 图像数组
        支持 RAW、TIFF、JPG、PNG 格式

        Args:
            raw_path: 图像文件路径
            white_balance: 白平衡模式 ('camera', 'daylight', 'auto') - 仅对 RAW 有效
            exposure_compensation: 曝光补偿（-3.0 到 +3.0 EV） - 仅对 RAW 有效
            **kwargs: 其他 rawpy 参数

        Returns:
            RGB 图像数组 (height, width, 3)，16-bit

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        if not raw_path.exists():
            raise FileNotFoundError(f"文件不存在: {raw_path}")

        if not self.is_supported_file(raw_path):
            raise ValueError(f"不支持的文件格式: {raw_path.suffix}")

        suffix = raw_path.suffix.lower()

        # 如果是 RAW 格式，使用 rawpy 处理
        if suffix in self.SUPPORTED_RAW_FORMATS:
            # 准备处理参数
            params = self.default_params.copy()
            params.update(kwargs)

            # 设置白平衡
            if white_balance == "camera":
                params["use_camera_wb"] = True
            elif white_balance == "daylight":
                params["use_camera_wb"] = False
                params["use_auto_wb"] = False
            elif white_balance == "auto":
                params["use_camera_wb"] = False
                params["use_auto_wb"] = True

            # 设置曝光补偿（2^EV）
            params["exp_shift"] = 2.0**exposure_compensation

            # 处理 RAW 文件
            with rawpy.imread(str(raw_path)) as raw:
                rgb = raw.postprocess(**params)

            return rgb

        # 如果是 TIFF、JPG、PNG 等格式，使用 PIL 读取
        else:
            img = Image.open(raw_path)

            # 转换为 RGB（如果不是）
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 转换为 numpy 数组
            rgb = np.array(img)

            # 如果是 8-bit，转换为 16-bit
            if rgb.dtype == np.uint8:
                rgb = (rgb.astype(np.uint16) * 257)  # 8-bit -> 16-bit

            return rgb

    def get_thumbnail(
        self, raw_path: Path, max_size: int = 512
    ) -> Optional[np.ndarray]:
        """
        获取 RAW 文件的缩略图

        Args:
            raw_path: RAW 文件路径
            max_size: 缩略图最大尺寸

        Returns:
            缩略图数组或 None
        """
        try:
            with rawpy.imread(str(raw_path)) as raw:
                # 尝试提取嵌入的 JPEG 缩略图
                try:
                    thumb = raw.extract_thumb()
                    if thumb.format == rawpy.ThumbFormat.JPEG:
                        # 将 JPEG 数据转换为数组
                        from io import BytesIO

                        img = Image.open(BytesIO(thumb.data))
                        img.thumbnail((max_size, max_size), Image.LANCZOS)
                        return np.array(img)
                except rawpy.LibRawError:
                    pass

                # 如果没有缩略图，处理低分辨率版本
                rgb = raw.postprocess(
                    half_size=True,  # 使用一半尺寸加速
                    use_camera_wb=True,
                    output_bps=8,
                )
                img = Image.fromarray(rgb)
                img.thumbnail((max_size, max_size), Image.LANCZOS)
                return np.array(img)

        except Exception as e:
            print(f"获取缩略图失败: {e}")
            return None

    def get_metadata(self, raw_path: Path) -> Dict[str, Any]:
        """
        获取 RAW 文件的元数据

        Args:
            raw_path: RAW 文件路径

        Returns:
            包含元数据的字典
        """
        metadata = {}
        try:
            with rawpy.imread(str(raw_path)) as raw:
                metadata["camera"] = raw.camera_model
                metadata["iso"] = raw.camera_iso
                metadata["shutter_speed"] = raw.camera_shutter_speed
                metadata["aperture"] = raw.camera_aperture
                metadata["focal_length"] = raw.camera_focal_length
                metadata["width"] = raw.sizes.width
                metadata["height"] = raw.sizes.height
        except Exception as e:
            print(f"读取元数据失败: {e}")

        return metadata


# 示例用法
if __name__ == "__main__":
    processor = RawProcessor()

    # 测试文件检查
    test_file = Path("test.nef")
    print(f"是否为 RAW 文件: {processor.is_raw_file(test_file)}")
