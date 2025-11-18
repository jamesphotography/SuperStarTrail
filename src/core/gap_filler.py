"""
from utils.logger import setup_logger

logger = setup_logger(__name__)

星轨间隔填充模块

用于填补星轨之间的间隔，使星轨更加连续流畅
"""

from typing import List, Tuple, Optional
import numpy as np
from scipy import ndimage
from numba import jit


class GapFiller:
    """星轨间隔填充器"""

    def __init__(self, method: str = "morphological"):
        """
        初始化间隔填充器

        Args:
            method: 填充方法
                - 'morphological': 形态学闭运算（默认，适合弧形星轨）
                - 'directional': 方向自适应填充（推荐用于弧形星轨）
                - 'linear': 线性插值
                - 'motion_blur': 运动模糊
        """
        self.method = method

    def fill_gaps(
        self,
        image: np.ndarray,
        gap_size: int = 3,
        intensity_threshold: float = 0.1,
    ) -> np.ndarray:
        """
        填充星轨间隔

        Args:
            image: 输入图像 (H, W, 3) 或 (H, W)
            gap_size: 要填充的最大间隔大小（像素）
            intensity_threshold: 亮度阈值，低于此值的被认为是间隔

        Returns:
            填充后的图像
        """
        if self.method == "linear":
            return self._linear_fill(image, gap_size, intensity_threshold)
        elif self.method == "morphological":
            return self._morphological_fill(image, gap_size)
        elif self.method == "motion_blur":
            return self._motion_blur_fill(image, gap_size)
        elif self.method == "directional":
            return self._directional_fill(image, gap_size)
        else:
            raise ValueError(f"未知的填充方法: {self.method}")

    def _linear_fill(
        self,
        image: np.ndarray,
        gap_size: int,
        intensity_threshold: float,
    ) -> np.ndarray:
        """
        线性插值填充

        在检测到的星轨间隔处进行线性插值
        """
        result = image.copy()

        # 处理每个通道
        if len(image.shape) == 3:
            for c in range(image.shape[2]):
                result[:, :, c] = self._fill_channel_linear(
                    image[:, :, c], gap_size, intensity_threshold
                )
        else:
            result = self._fill_channel_linear(image, gap_size, intensity_threshold)

        return result

    @staticmethod
    @jit(nopython=True)
    def _fill_channel_linear(
        channel: np.ndarray,
        gap_size: int,
        intensity_threshold: float,
    ) -> np.ndarray:
        """
        对单个通道进行线性填充（JIT 加速）

        Args:
            channel: 单通道图像
            gap_size: 间隔大小
            intensity_threshold: 亮度阈值（归一化到 0-1）

        Returns:
            填充后的通道
        """
        result = channel.copy()
        h, w = channel.shape

        # 归一化到 0-1
        max_val = np.max(channel)
        if max_val > 0:
            normalized = channel.astype(np.float32) / max_val
        else:
            return result

        # 水平方向填充（星轨主要是水平的）
        for y in range(h):
            x = 0
            while x < w:
                # 找到亮点
                if normalized[y, x] > intensity_threshold:
                    start_x = x
                    # 找到下一个亮点或间隔
                    x += 1
                    gap_start = -1

                    while x < w:
                        if normalized[y, x] <= intensity_threshold:
                            if gap_start == -1:
                                gap_start = x
                            x += 1
                        else:
                            # 找到间隔后的下一个亮点
                            if gap_start != -1:
                                gap_end = x
                                gap_length = gap_end - gap_start

                                # 如果间隔不太大，进行插值
                                if gap_length <= gap_size and gap_start > start_x:
                                    # 线性插值
                                    start_val = channel[y, gap_start - 1]
                                    end_val = channel[y, gap_end]

                                    for gx in range(gap_start, gap_end):
                                        alpha = (gx - gap_start + 1) / (gap_length + 1)
                                        result[y, gx] = start_val * (1 - alpha) + end_val * alpha

                            break
                else:
                    x += 1

        return result

    def _morphological_fill(self, image: np.ndarray, gap_size: int) -> np.ndarray:
        """
        形态学闭运算填充

        使用形态学闭运算来连接断开的星轨
        自适应处理不同方向的星轨（包括弧形）
        """
        result = image.copy()

        # 创建圆形结构元素，而不是只用水平方向
        # 这样可以处理各个方向的星轨
        size = gap_size * 2 + 1
        y, x = np.ogrid[-gap_size:gap_size+1, -gap_size:gap_size+1]

        # 椭圆形结构元素，稍微拉长以适应星轨
        # 使用更大的水平范围来捕捉星轨的主要运动方向
        kernel = (x*x / (gap_size * 1.5)**2 + y*y / gap_size**2) <= 1
        kernel = kernel.astype(np.uint8)

        # 处理每个通道
        if len(image.shape) == 3:
            for c in range(image.shape[2]):
                # 形态学闭运算 = 膨胀 + 腐蚀
                dilated = ndimage.grey_dilation(image[:, :, c], footprint=kernel)
                result[:, :, c] = ndimage.grey_erosion(dilated, footprint=kernel)
        else:
            dilated = ndimage.grey_dilation(image, footprint=kernel)
            result = ndimage.grey_erosion(dilated, footprint=kernel)

        return result

    def _motion_blur_fill(self, image: np.ndarray, gap_size: int) -> np.ndarray:
        """
        运动模糊填充

        使用定向运动模糊来平滑星轨间隔
        """
        result = image.copy()

        # 创建水平运动模糊核
        kernel = np.zeros((1, gap_size * 2 + 1))
        kernel[0, :] = 1.0 / kernel.shape[1]

        # 处理每个通道
        if len(image.shape) == 3:
            for c in range(image.shape[2]):
                result[:, :, c] = ndimage.convolve(
                    image[:, :, c], kernel, mode="constant"
                )
        else:
            result = ndimage.convolve(image, kernel, mode="constant")

        return result

    def _directional_fill(self, image: np.ndarray, gap_size: int) -> np.ndarray:
        """
        方向自适应填充

        专门用于弧形星轨，使用多个方向的形态学操作
        """
        result = image.copy()

        # 定义多个角度的结构元素
        angles = [0, 30, 60, 90, 120, 150]  # 覆盖不同方向的星轨

        # 对每个通道处理
        if len(image.shape) == 3:
            for c in range(image.shape[2]):
                channel_result = image[:, :, c].copy()

                # 对每个角度应用形态学闭运算
                for angle in angles:
                    # 创建旋转的线性结构元素
                    kernel = self._create_rotated_kernel(gap_size, angle)

                    # 形态学闭运算
                    dilated = ndimage.grey_dilation(image[:, :, c], footprint=kernel)
                    closed = ndimage.grey_erosion(dilated, footprint=kernel)

                    # 取最大值（保留所有方向的连接）
                    channel_result = np.maximum(channel_result, closed)

                result[:, :, c] = channel_result
        else:
            channel_result = image.copy()

            for angle in angles:
                kernel = self._create_rotated_kernel(gap_size, angle)
                dilated = ndimage.grey_dilation(image, footprint=kernel)
                closed = ndimage.grey_erosion(dilated, footprint=kernel)
                channel_result = np.maximum(channel_result, closed)

            result = channel_result

        return result

    @staticmethod
    def _create_rotated_kernel(gap_size: int, angle: float) -> np.ndarray:
        """
        创建旋转的线性结构元素

        Args:
            gap_size: 间隔大小
            angle: 旋转角度（度）

        Returns:
            旋转的结构元素
        """
        size = gap_size * 4 + 1
        kernel = np.zeros((size, size), dtype=np.uint8)

        # 计算中心
        center = size // 2

        # 转换角度为弧度
        rad = np.radians(angle)

        # 绘制旋转的线
        length = gap_size * 2
        for i in range(-length, length + 1):
            x = int(center + i * np.cos(rad))
            y = int(center + i * np.sin(rad))

            if 0 <= x < size and 0 <= y < size:
                kernel[y, x] = 1

        # 稍微扩展线条以增加连接强度
        kernel = ndimage.binary_dilation(kernel, iterations=1).astype(np.uint8)

        return kernel

    def detect_star_trails(
        self, image: np.ndarray, brightness_threshold: float = 0.3
    ) -> np.ndarray:
        """
        检测星轨位置

        Args:
            image: 输入图像
            brightness_threshold: 亮度阈值（0-1）

        Returns:
            二值掩码，星轨区域为 True
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = np.mean(image, axis=2)
        else:
            gray = image

        # 归一化
        normalized = gray.astype(np.float32) / np.max(gray)

        # 阈值化
        mask = normalized > brightness_threshold

        return mask

    def adaptive_fill(
        self,
        image: np.ndarray,
        min_gap: int = 1,
        max_gap: int = 5,
        brightness_threshold: float = 0.1,
    ) -> np.ndarray:
        """
        自适应填充

        根据图像内容自动调整填充参数

        Args:
            image: 输入图像
            min_gap: 最小间隔大小
            max_gap: 最大间隔大小
            brightness_threshold: 亮度阈值

        Returns:
            填充后的图像
        """
        # 检测星轨
        trail_mask = self.detect_star_trails(image, brightness_threshold)

        # 计算平均星轨宽度
        if len(image.shape) == 3:
            gray = np.mean(image, axis=2)
        else:
            gray = image

        # 估计合适的间隔大小
        # 这里使用简单的启发式方法
        estimated_gap = min(max_gap, max(min_gap, 3))

        # 应用填充
        return self.fill_gaps(image, gap_size=estimated_gap, intensity_threshold=brightness_threshold)


class StarTrailSmoother:
    """星轨平滑器 - 更高级的间隔填充"""

    def __init__(self):
        """初始化平滑器"""
        pass

    def smooth_trails(
        self,
        image: np.ndarray,
        window_size: int = 5,
        sigma: float = 1.0,
    ) -> np.ndarray:
        """
        使用高斯平滑处理星轨

        Args:
            image: 输入图像
            window_size: 平滑窗口大小
            sigma: 高斯核标准差

        Returns:
            平滑后的图像
        """
        result = image.copy()

        # 创建各向异性高斯核（水平方向更强）
        if len(image.shape) == 3:
            for c in range(image.shape[2]):
                result[:, :, c] = ndimage.gaussian_filter(
                    image[:, :, c], sigma=[sigma / 2, sigma * 2]
                )
        else:
            result = ndimage.gaussian_filter(image, sigma=[sigma / 2, sigma * 2])

        # 与原图混合，保留亮度
        alpha = 0.7  # 原图权重
        result = image * alpha + result * (1 - alpha)

        return result.astype(image.dtype)

    def enhance_continuity(
        self,
        image: np.ndarray,
        iterations: int = 2,
    ) -> np.ndarray:
        """
        增强星轨连续性

        Args:
            image: 输入图像
            iterations: 迭代次数

        Returns:
            增强后的图像
        """
        result = image.copy()

        for _ in range(iterations):
            # 形态学闭运算
            filler = GapFiller(method="morphological")
            result = filler.fill_gaps(result, gap_size=3)

            # 轻微平滑
            result = self.smooth_trails(result, window_size=3, sigma=0.5)

        return result


# 示例用法
if __name__ == "__main__":
    # 创建测试图像（模拟带间隔的星轨）
    test_img = np.zeros((100, 200, 3), dtype=np.uint16)

    # 绘制一些模拟星轨（带间隔）
    for i in range(10, 90, 10):
        for j in range(0, 200, 15):  # 每隔 15 像素画 10 像素的亮点
            if j + 10 < 200:
                test_img[i, j : j + 10, :] = 50000  # 亮点

    logger.info("创建测试图像")
    logger.info(f"图像形状: {test_img.shape}")

    # 测试线性填充
    logger.info("\n测试线性填充...")
    filler_linear = GapFiller(method="linear")
    result_linear = filler_linear.fill_gaps(test_img, gap_size=5, intensity_threshold=0.1)
    logger.info(f"填充完成，结果形状: {result_linear.shape}")

    # 测试形态学填充
    logger.info("\n测试形态学填充...")
    filler_morph = GapFiller(method="morphological")
    result_morph = filler_morph.fill_gaps(test_img, gap_size=3)
    logger.info(f"填充完成，结果形状: {result_morph.shape}")

    # 测试平滑器
    logger.info("\n测试星轨平滑...")
    smoother = StarTrailSmoother()
    result_smooth = smoother.smooth_trails(test_img, window_size=5, sigma=1.0)
    logger.info(f"平滑完成，结果形状: {result_smooth.shape}")

    logger.info("\n✅ 所有测试完成！")
