"""
图像堆栈引擎模块

实现各种图像堆栈算法，包括星轨合成、降噪等
"""

from enum import Enum
from typing import List, Optional, Callable
import numpy as np
from numba import jit


class StackMode(Enum):
    """堆栈模式枚举"""

    LIGHTEN = "lighten"  # 最大值 - 用于星轨
    DARKEN = "darken"  # 最小值 - 用于去除光污染
    AVERAGE = "average"  # 平均值 - 用于降噪
    MEDIAN = "median"  # 中值 - 用于去除热像素
    ADDITION = "addition"  # 叠加 - 累积曝光
    COMET = "comet"  # 彗星模式 - 渐变尾迹


@jit(nopython=True)
def _fast_maximum(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    JIT 加速的最大值运算

    Args:
        a: 第一个数组
        b: 第二个数组

    Returns:
        逐元素最大值
    """
    return np.maximum(a, b)


@jit(nopython=True)
def _fast_minimum(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    JIT 加速的最小值运算

    Args:
        a: 第一个数组
        b: 第二个数组

    Returns:
        逐元素最小值
    """
    return np.minimum(a, b)


class StackingEngine:
    """图像堆栈引擎"""

    def __init__(
        self,
        mode: StackMode = StackMode.LIGHTEN,
        enable_alignment: bool = False,
        enable_gap_filling: bool = False,
        gap_fill_method: str = "morphological",
        gap_size: int = 3,
    ):
        """
        初始化堆栈引擎

        Args:
            mode: 堆栈模式
            enable_alignment: 是否启用图像对齐（修正相机抖动）
            enable_gap_filling: 是否启用间隔填充（消除星轨间隔）
            gap_fill_method: 填充方法 ('linear', 'morphological', 'motion_blur')
            gap_size: 要填充的最大间隔大小（像素）
        """
        self.mode = mode
        self.result: Optional[np.ndarray] = None
        self.reference: Optional[np.ndarray] = None  # 参考图像用于对齐
        self.count = 0
        self.comet_fade_factor = 0.98  # 彗星模式的衰减因子
        self.enable_alignment = enable_alignment
        self.aligner = None
        self.enable_gap_filling = enable_gap_filling
        self.gap_filler = None
        self.gap_fill_method = gap_fill_method
        self.gap_size = gap_size

        # 如果启用对齐，初始化对齐器
        if enable_alignment:
            try:
                from .image_aligner import ImageAligner
                self.aligner = ImageAligner(method="orb")  # 使用快速的 ORB
            except ImportError:
                print("警告: OpenCV 未安装，图像对齐功能不可用")
                self.enable_alignment = False

        # 如果启用间隔填充，初始化填充器
        if enable_gap_filling:
            try:
                from .gap_filler import GapFiller
                self.gap_filler = GapFiller(method=gap_fill_method)
            except ImportError as e:
                print(f"警告: scipy 未安装，间隔填充功能不可用 ({e})")
                self.enable_gap_filling = False

    def reset(self):
        """重置引擎状态"""
        self.result = None
        self.count = 0

    def add_image(
        self,
        image: np.ndarray,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> np.ndarray:
        """
        添加一张图像到堆栈

        Args:
            image: 输入图像数组 (H, W, 3)
            progress_callback: 进度回调函数，接收当前处理的图像数量

        Returns:
            当前堆栈结果的副本
        """
        # 如果启用对齐且不是第一张图像
        if self.enable_alignment and self.reference is not None:
            if self.aligner is not None:
                # 对齐图像
                image, success = self.aligner.align(image, self.reference, max_shift=50)
                if not success:
                    print(f"警告: 第 {self.count + 1} 张图像对齐失败，使用原图")

        # 转换为 float32 以避免溢出
        img_float = image.astype(np.float32)

        if self.result is None:
            # 第一张图像，直接作为初始结果和参考
            self.result = img_float.copy()
            if self.enable_alignment:
                self.reference = image.copy()  # 保存为参考图像
        else:
            # 根据模式进行堆栈
            if self.mode == StackMode.LIGHTEN:
                self.result = _fast_maximum(self.result, img_float)

            elif self.mode == StackMode.DARKEN:
                self.result = _fast_minimum(self.result, img_float)

            elif self.mode == StackMode.AVERAGE:
                # 增量平均：new_avg = (old_avg * count + new_value) / (count + 1)
                self.result = (self.result * self.count + img_float) / (
                    self.count + 1
                )

            elif self.mode == StackMode.MEDIAN:
                # 中值模式需要保存所有图像，这里暂不实现
                raise NotImplementedError("中值模式需要在批量处理中实现")

            elif self.mode == StackMode.ADDITION:
                # 叠加模式需要注意溢出
                self.result = self.result + img_float

            elif self.mode == StackMode.COMET:
                # 彗星模式：当前结果衰减，新图像添加
                self.result = (
                    self.result * self.comet_fade_factor
                    + img_float * (1 - self.comet_fade_factor)
                )

        self.count += 1

        # 调用进度回调
        if progress_callback:
            progress_callback(self.count)

        # 返回当前结果的简单副本，不应用填充
        # 填充只应该在最终 get_result() 时应用一次
        return self.result.astype(np.uint16)

    def get_result(self, normalize: bool = False, apply_gap_filling: bool = True) -> np.ndarray:
        """
        获取当前堆栈结果

        Args:
            normalize: 是否归一化到原始位深
            apply_gap_filling: 是否应用间隔填充（默认 True，预览时应设为 False）

        Returns:
            堆栈结果数组
        """
        if self.result is None:
            raise ValueError("还没有添加任何图像")

        result = self.result.copy()

        # 对于 Addition 模式，可能需要归一化
        if normalize or self.mode == StackMode.ADDITION:
            # 裁剪到有效范围
            result = np.clip(result, 0, 65535)

        # 应用间隔填充（如果启用且需要）
        if apply_gap_filling and self.enable_gap_filling and self.gap_filler is not None:
            print(f"应用间隔填充 (方法: {self.gap_fill_method}, 间隔大小: {self.gap_size})")
            result_uint16 = result.astype(np.uint16)
            result_filled = self.gap_filler.fill_gaps(
                result_uint16,
                gap_size=self.gap_size,
                intensity_threshold=0.1,
            )
            return result_filled.astype(np.uint16)

        return result.astype(np.uint16)

    def process_batch(
        self,
        images: List[np.ndarray],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> np.ndarray:
        """
        批量处理多张图像

        Args:
            images: 图像列表
            progress_callback: 进度回调函数，接收 (当前索引, 总数)

        Returns:
            最终堆栈结果
        """
        self.reset()
        total = len(images)

        for i, img in enumerate(images):
            self.add_image(img)

            if progress_callback:
                progress_callback(i + 1, total)

        return self.get_result()

    def process_median(self, images: List[np.ndarray]) -> np.ndarray:
        """
        中值堆栈（需要所有图像在内存中）

        Args:
            images: 图像列表

        Returns:
            中值堆栈结果
        """
        if not images:
            raise ValueError("图像列表为空")

        # 将所有图像堆叠成 4D 数组 (N, H, W, C)
        stack = np.stack(images, axis=0).astype(np.float32)

        # 沿着第一个轴（图像数量）计算中值
        result = np.median(stack, axis=0)

        return result.astype(np.uint16)

    def set_comet_fade_factor(self, factor: float):
        """
        设置彗星模式的衰减因子

        Args:
            factor: 衰减因子 (0.0-1.0)，越接近1尾迹越长
        """
        if not 0.0 <= factor <= 1.0:
            raise ValueError("衰减因子必须在 0.0 到 1.0 之间")
        self.comet_fade_factor = factor


class DarkFrameSubtractor:
    """暗帧减除器"""

    def __init__(self, dark_frame: np.ndarray):
        """
        初始化暗帧减除器

        Args:
            dark_frame: 暗帧图像
        """
        self.dark_frame = dark_frame.astype(np.float32)

    def subtract(self, image: np.ndarray) -> np.ndarray:
        """
        从图像中减除暗帧

        Args:
            image: 输入图像

        Returns:
            减除暗帧后的图像
        """
        result = image.astype(np.float32) - self.dark_frame
        result = np.clip(result, 0, 65535)
        return result.astype(np.uint16)


# 示例用法
if __name__ == "__main__":
    # 创建测试图像
    img1 = np.random.randint(0, 32768, (100, 100, 3), dtype=np.uint16)
    img2 = np.random.randint(0, 32768, (100, 100, 3), dtype=np.uint16)
    img3 = np.random.randint(0, 32768, (100, 100, 3), dtype=np.uint16)

    # 测试 Lighten 模式
    engine = StackingEngine(StackMode.LIGHTEN)
    engine.add_image(img1)
    engine.add_image(img2)
    engine.add_image(img3)
    result = engine.get_result()

    print(f"处理了 {engine.count} 张图像")
    print(f"结果形状: {result.shape}")
    print(f"结果数据类型: {result.dtype}")
