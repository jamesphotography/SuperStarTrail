"""
from utils.logger import setup_logger

logger = setup_logger(__name__)

图像导出模块

负责将处理后的图像保存为各种格式
"""

from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image
import tifffile


class ImageExporter:
    """图像导出器"""

    @staticmethod
    def apply_stretch(image: np.ndarray, p_low: float = 1.0, p_high: float = 99.5) -> np.ndarray:
        """
        应用百分位数拉伸到图像

        Args:
            image: 输入图像 (uint16)
            p_low: 低百分位数 (默认 1%)
            p_high: 高百分位数 (默认 99.5%)

        Returns:
            拉伸后的图像 (uint16)
        """
        if image.dtype != np.uint16:
            return image

        # 计算百分位数
        low_val = np.percentile(image, p_low)
        high_val = np.percentile(image, p_high)

        # 拉伸到 0-65535
        stretched = np.clip((image - low_val) / (high_val - low_val) * 65535, 0, 65535)

        return stretched.astype(np.uint16)

    @staticmethod
    def save_tiff(
        image: np.ndarray,
        output_path: Path,
        bits: int = 16,
        compression: str = "lzw",
        apply_stretch: bool = True,
    ) -> bool:
        """
        保存为 TIFF 格式

        Args:
            image: 图像数组
            output_path: 输出路径
            bits: 位深度 (8, 16, 32)
            compression: 压缩方式 ('none', 'lzw', 'jpeg', 'deflate')
            apply_stretch: 是否应用百分位数拉伸（默认 True）

        Returns:
            保存是否成功
        """
        try:
            # 如果需要，先应用拉伸
            if apply_stretch and image.dtype == np.uint16:
                logger.warning("应用亮度拉伸 (1%-99.5%)...")
                image = ImageExporter.apply_stretch(image)

            if bits == 8:
                # 转换为 8-bit
                if image.dtype == np.uint16:
                    img_to_save = (image / 256).astype(np.uint8)
                else:
                    img_to_save = image.astype(np.uint8)
            elif bits == 16:
                img_to_save = image.astype(np.uint16)
            elif bits == 32:
                # 32-bit 浮点
                img_to_save = image.astype(np.float32) / 65535.0
            else:
                raise ValueError(f"不支持的位深度: {bits}")

            # 使用 tifffile 保存（支持更好的元数据）
            # 如果 LZW 压缩失败，尝试无压缩
            try:
                tifffile.imwrite(
                    str(output_path),
                    img_to_save,
                    compression=compression,
                    photometric="rgb" if image.ndim == 3 else "minisblack",
                )
            except Exception as e:
                if "imagecodecs" in str(e):
                    # 降级到无压缩
                    print(f"警告: {compression} 压缩需要 imagecodecs 包，使用无压缩模式")
                    tifffile.imwrite(
                        str(output_path),
                        img_to_save,
                        compression=None,
                        photometric="rgb" if image.ndim == 3 else "minisblack",
                    )
                else:
                    raise

            return True

        except Exception as e:
            logger.info(f"保存 TIFF 失败: {e}")
            return False

    @staticmethod
    def save_jpeg(
        image: np.ndarray, output_path: Path, quality: int = 95
    ) -> bool:
        """
        保存为 JPEG 格式

        Args:
            image: 图像数组
            output_path: 输出路径
            quality: JPEG 质量 (1-100)

        Returns:
            保存是否成功
        """
        try:
            # JPEG 只支持 8-bit
            if image.dtype == np.uint16:
                img_8bit = (image / 256).astype(np.uint8)
            else:
                img_8bit = image.astype(np.uint8)

            img = Image.fromarray(img_8bit)
            img.save(output_path, "JPEG", quality=quality, optimize=True)

            return True

        except Exception as e:
            logger.info(f"保存 JPEG 失败: {e}")
            return False

    @staticmethod
    def save_png(image: np.ndarray, output_path: Path, compress_level: int = 6) -> bool:
        """
        保存为 PNG 格式

        Args:
            image: 图像数组
            output_path: 输出路径
            compress_level: 压缩级别 (0-9)

        Returns:
            保存是否成功
        """
        try:
            # PNG 支持 8-bit 和 16-bit
            if image.dtype == np.uint16:
                # 保持 16-bit
                img = Image.fromarray(image, mode="I;16")
            else:
                img = Image.fromarray(image.astype(np.uint8))

            img.save(output_path, "PNG", compress_level=compress_level)

            return True

        except Exception as e:
            logger.info(f"保存 PNG 失败: {e}")
            return False

    @staticmethod
    def save_auto(
        image: np.ndarray,
        output_path: Path,
        quality: int = 95,
        **kwargs,
    ) -> bool:
        """
        根据文件扩展名自动选择保存格式

        Args:
            image: 图像数组
            output_path: 输出路径
            quality: 质量参数（用于 JPEG）
            **kwargs: 其他参数

        Returns:
            保存是否成功
        """
        ext = output_path.suffix.lower()

        if ext in [".tif", ".tiff"]:
            return ImageExporter.save_tiff(image, output_path, **kwargs)
        elif ext in [".jpg", ".jpeg"]:
            return ImageExporter.save_jpeg(image, output_path, quality=quality)
        elif ext == ".png":
            return ImageExporter.save_png(image, output_path, **kwargs)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")


# 示例用法
if __name__ == "__main__":
    # 创建测试图像
    test_img = np.random.randint(0, 65535, (1000, 1000, 3), dtype=np.uint16)

    exporter = ImageExporter()

    # 测试保存
    logger.info("测试保存 TIFF...")
    success = exporter.save_tiff(test_img, Path("test_output.tiff"))
    logger.info(f"TIFF 保存: {'成功' if success else '失败'}")
