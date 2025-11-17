"""
延时视频生成器

负责将星轨堆栈的中间过程保存为延时视频
"""

import numpy as np
import cv2
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TimelapseGenerator:
    """延时视频生成器"""

    def __init__(
        self,
        output_path: Path,
        fps: int = 25,
        resolution: Tuple[int, int] = (3840, 2160),  # 4K
        temp_dir: Optional[Path] = None
    ):
        """
        初始化延时视频生成器

        Args:
            output_path: 输出视频路径（.mp4）
            fps: 帧率（默认 25 FPS）
            resolution: 视频分辨率（默认 4K）
            temp_dir: 临时帧目录（如果不指定，使用 output_path 同级目录）
        """
        self.output_path = Path(output_path)
        self.fps = fps
        self.resolution = resolution  # (width, height)

        # 临时目录
        if temp_dir is None:
            self.temp_dir = self.output_path.parent / f"{self.output_path.stem}_frames"
        else:
            self.temp_dir = Path(temp_dir)

        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.frame_count = 0
        self.frame_paths = []

        logger.info(f"延时视频生成器初始化: {self.fps} FPS, {self.resolution[0]}×{self.resolution[1]}")
        logger.info(f"临时帧目录: {self.temp_dir}")

    def add_frame(self, image: np.ndarray) -> None:
        """
        添加一帧到延时视频

        Args:
            image: 16-bit 图像 (H, W, 3)
        """
        # 转换为 8-bit（使用 percentile-based 拉伸，和预览一样）
        img_8bit = self._convert_to_8bit(image)

        # 调整尺寸到 4K 16:9（中心裁切）
        img_resized = self._resize_to_target(img_8bit)

        # 保存为 JPEG
        frame_path = self.temp_dir / f"frame_{self.frame_count:05d}.jpg"
        cv2.imwrite(str(frame_path), cv2.cvtColor(img_resized, cv2.COLOR_RGB2BGR),
                    [cv2.IMWRITE_JPEG_QUALITY, 90])

        self.frame_paths.append(frame_path)
        self.frame_count += 1

        if self.frame_count % 10 == 0:
            logger.info(f"已保存第 {self.frame_count} 帧")

    def _convert_to_8bit(self, image: np.ndarray) -> np.ndarray:
        """
        将 16-bit 图像转换为 8-bit（使用 percentile-based 拉伸）

        Args:
            image: 16-bit 图像

        Returns:
            8-bit 图像
        """
        if image.dtype == np.uint16:
            # 使用百分位数拉伸，避免过暗或过曝
            p_low = np.percentile(image, 1)
            p_high = np.percentile(image, 99.5)

            # 拉伸到 0-255
            img_stretched = np.clip((image - p_low) / (p_high - p_low) * 255, 0, 255)
            img_8bit = img_stretched.astype(np.uint8)
        else:
            img_8bit = image

        return img_8bit

    def _resize_to_target(self, image: np.ndarray) -> np.ndarray:
        """
        将图像调整到目标分辨率（16:9，中心裁切）

        Args:
            image: 8-bit RGB 图像 (H, W, 3)

        Returns:
            调整后的图像
        """
        h, w = image.shape[:2]
        target_w, target_h = self.resolution
        target_ratio = target_w / target_h  # 16:9 = 1.777...
        current_ratio = w / h

        # 中心裁切到 16:9
        if current_ratio > target_ratio:
            # 图像太宽，裁切左右
            new_w = int(h * target_ratio)
            x_offset = (w - new_w) // 2
            cropped = image[:, x_offset:x_offset + new_w]
        else:
            # 图像太高，裁切上下
            new_h = int(w / target_ratio)
            y_offset = (h - new_h) // 2
            cropped = image[y_offset:y_offset + new_h, :]

        # 缩放到目标分辨率
        resized = cv2.resize(cropped, self.resolution, interpolation=cv2.INTER_AREA)

        return resized

    def generate_video(self, cleanup: bool = True) -> bool:
        """
        从保存的帧生成视频

        Args:
            cleanup: 是否删除临时帧文件

        Returns:
            是否成功
        """
        if self.frame_count == 0:
            logger.error("没有帧可以生成视频")
            return False

        logger.info(f"开始生成视频: {self.output_path}")
        logger.info(f"总帧数: {self.frame_count}, 时长: {self.frame_count / self.fps:.2f} 秒")

        try:
            # 使用 OpenCV 创建视频编码器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4 编码器
            video = cv2.VideoWriter(
                str(self.output_path),
                fourcc,
                self.fps,
                self.resolution
            )

            # 逐帧写入
            for i, frame_path in enumerate(self.frame_paths):
                frame = cv2.imread(str(frame_path))
                video.write(frame)

                if (i + 1) % 10 == 0:
                    logger.info(f"编码进度: {i + 1}/{self.frame_count} 帧")

            video.release()
            logger.info(f"视频生成成功: {self.output_path}")

            # 清理临时文件
            if cleanup:
                self.cleanup_temp_files()

            return True

        except Exception as e:
            logger.error(f"视频生成失败: {e}", exc_info=True)
            return False

    def cleanup_temp_files(self) -> None:
        """删除临时帧文件"""
        logger.info(f"清理临时文件: {self.temp_dir}")

        try:
            for frame_path in self.frame_paths:
                if frame_path.exists():
                    frame_path.unlink()

            # 删除临时目录（如果为空）
            if self.temp_dir.exists() and not any(self.temp_dir.iterdir()):
                self.temp_dir.rmdir()
                logger.info("临时目录已删除")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

    def get_frame_count(self) -> int:
        """获取当前帧数"""
        return self.frame_count

    def get_duration(self) -> float:
        """获取视频时长（秒）"""
        return self.frame_count / self.fps
