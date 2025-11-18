"""
from utils.logger import setup_logger

logger = setup_logger(__name__)

蒙版工具模块

提供蒙版预览和简单处理功能
"""

from typing import Tuple
import numpy as np
from PIL import Image
import cv2


class MaskUtils:
    """蒙版工具类"""

    @staticmethod
    def create_preview_overlay(
        image: np.ndarray,
        mask: np.ndarray,
        overlay_color: Tuple[int, int, int] = (0, 255, 255),
        alpha: float = 0.3
    ) -> np.ndarray:
        """
        创建蒙版叠加预览图

        Args:
            image: 输入图像 (H, W, 3)，RGB，uint8 或 uint16
            mask: 蒙版 (H, W)，0-255
            overlay_color: 叠加颜色 (R, G, B)，0-255
            alpha: 叠加透明度 (0.0-1.0)

        Returns:
            叠加后的图像 (H, W, 3)，RGB，uint8（用于预览）
        """
        # 如果是 16-bit，转换为 8-bit
        if image.dtype == np.uint16:
            img_8bit = (image / 256).astype(np.uint8)
        else:
            img_8bit = image.copy()

        # 创建彩色叠加层
        overlay = np.zeros_like(img_8bit)
        overlay[mask > 127] = overlay_color

        # 混合
        result = cv2.addWeighted(img_8bit, 1 - alpha, overlay, alpha, 0)

        return result

    @staticmethod
    def feather_mask(
        mask: np.ndarray,
        radius: int = 10
    ) -> np.ndarray:
        """
        羽化蒙版边缘

        Args:
            mask: 输入蒙版 (H, W)，0-255
            radius: 羽化半径（像素）

        Returns:
            羽化后的蒙版 (H, W)，0-255
        """
        if radius <= 0:
            return mask

        # 转换为浮点数
        mask_float = mask.astype(np.float32) / 255.0

        # 高斯模糊
        kernel_size = radius * 2 + 1
        mask_feathered = cv2.GaussianBlur(
            mask_float,
            (kernel_size, kernel_size),
            radius / 2
        )

        # 转换回 uint8
        return (mask_feathered * 255).astype(np.uint8)

    @staticmethod
    def save_mask_comparison(
        original_image: np.ndarray,
        mask: np.ndarray,
        output_path: str
    ):
        """
        保存原图和蒙版的对比图

        Args:
            original_image: 原始图像 (H, W, 3)
            mask: 蒙版 (H, W)
            output_path: 输出路径
        """
        # 转换为 8-bit
        if original_image.dtype == np.uint16:
            img_8bit = (original_image / 256).astype(np.uint8)
        else:
            img_8bit = original_image

        # 创建叠加预览
        overlay = MaskUtils.create_preview_overlay(
            img_8bit,
            mask,
            overlay_color=(0, 255, 255),
            alpha=0.4
        )

        # 并排显示：原图 | 蒙版 | 叠加
        h, w = mask.shape
        mask_rgb = np.stack([mask, mask, mask], axis=2)

        # 水平拼接
        comparison = np.hstack([img_8bit, mask_rgb, overlay])

        # 保存
        Image.fromarray(comparison).save(output_path)


if __name__ == '__main__':
    """测试代码"""
    logger.info("MaskUtils 工具模块")
    logger.info("提供蒙版预览和基本处理功能")
