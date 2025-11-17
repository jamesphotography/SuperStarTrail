"""
天空/地景分割模块

使用 SegFormer 模型进行语义分割，支持天空检测和多类别分割
"""

from typing import Optional, Tuple
import numpy as np
from PIL import Image
import torch
import cv2


class SkyDetector:
    """
    使用 SegFormer 模型进行天空/地景分割

    相比 DeepLabv3，SegFormer 具有以下优势：
    - 更快的推理速度 (2-3倍)
    - 更小的模型体积 (B0: 14MB vs 200MB)
    - 更高的精度 (ADE20K mIoU 51.8% vs 45%)
    - 更灵活的多尺度处理
    """

    def __init__(self, model_size: str = "b0", device: Optional[str] = None):
        """
        初始化 SegFormer 模型

        Args:
            model_size: 模型大小，可选 'b0' (快速，3.7M参数) 或 'b2' (精确，25M参数)
            device: 计算设备，None 表示自动选择 (优先 GPU)
        """
        self.model_size = model_size
        self.model_name = f"nvidia/segformer-{model_size}-finetuned-ade-512-512"

        # 设置计算设备
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # 延迟加载模型（只在第一次使用时加载）
        self._model = None
        self._processor = None

        # ADE20K 数据集的类别索引
        self.sky_class_index = 2  # 天空
        self.building_class_index = 1  # 建筑
        self.tree_class_index = 4  # 树木

    def _ensure_model_loaded(self):
        """确保模型已加载（懒加载模式）"""
        if self._model is not None:
            return

        try:
            from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation

            print(f"正在加载 SegFormer-{self.model_size} 模型...")
            self._processor = SegformerImageProcessor.from_pretrained(self.model_name)
            self._model = SegformerForSemanticSegmentation.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()
            print(f"✅ SegFormer 模型加载成功 (设备: {self.device})")

        except ImportError:
            raise ImportError(
                "需要安装 transformers 库才能使用 SegFormer。\n"
                "请运行: pip install transformers"
            )

    def segment(self, image: Image.Image, enhance_bright_sky: bool = True) -> np.ndarray:
        """
        对输入图像进行天空分割

        Args:
            image: PIL 图像 (RGB)
            enhance_bright_sky: 是否增强亮天空区域检测（用于修正银河等亮区域的误判）

        Returns:
            天空蒙版 (H×W)，值为 0-255 的二值图像
            - 255: 天空区域
            - 0: 其他区域
        """
        self._ensure_model_loaded()

        # 记录原始尺寸
        original_size = image.size  # (width, height)

        # 预处理图像
        inputs = self._processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 推理
        with torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits  # (1, num_classes, H, W)

        # 上采样到原始尺寸
        upsampled_logits = torch.nn.functional.interpolate(
            logits,
            size=(original_size[1], original_size[0]),  # (height, width)
            mode="bilinear",
            align_corners=False
        )

        # 获取每个像素的预测类别
        pred_seg = upsampled_logits.argmax(dim=1)[0]  # (H, W)

        # 提取天空蒙版
        sky_mask = (pred_seg == self.sky_class_index).cpu().numpy()

        # 亮度增强：修正银河等亮天空区域的误判
        if enhance_bright_sky:
            sky_mask = self._enhance_bright_sky_regions(image, sky_mask)

        # 转换为 0-255 的 uint8
        sky_mask_uint8 = (sky_mask * 255).astype(np.uint8)

        return sky_mask_uint8

    def _enhance_bright_sky_regions(self, image: Image.Image, initial_mask: np.ndarray,
                                     brightness_threshold: int = 40) -> np.ndarray:
        """
        增强亮天空区域检测，修正银河等被误判为地景的区域

        原理：
        1. 在初始天空区域附近
        2. 亮度超过阈值的像素
        3. 大概率是银河、星云等天空特征，应该包含在天空蒙版中

        Args:
            image: 原始图像 (PIL Image)
            initial_mask: SegFormer 初始分割结果 (bool array)
            brightness_threshold: 亮度阈值 (0-255)，高于此值的像素被视为"亮区域"

        Returns:
            增强后的天空蒙版 (bool array)
        """
        import cv2

        # 转换为 numpy 数组
        img_array = np.array(image)

        # 计算亮度图（使用感知亮度公式）
        if len(img_array.shape) == 3:
            # RGB → 感知亮度 (ITU-R BT.709)
            brightness = (0.2126 * img_array[:, :, 0] +
                         0.7152 * img_array[:, :, 1] +
                         0.0722 * img_array[:, :, 2])
        else:
            brightness = img_array

        # 创建亮区域蒙版
        bright_mask = brightness > brightness_threshold

        # 膨胀初始天空蒙版，找到天空附近的区域
        kernel = np.ones((50, 50), np.uint8)
        sky_dilated = cv2.dilate(initial_mask.astype(np.uint8), kernel, iterations=1)

        # 组合条件：在天空附近 AND 亮度高
        bright_sky_correction = bright_mask & (sky_dilated > 0)

        # 合并到原始蒙版
        enhanced_mask = initial_mask | bright_sky_correction

        return enhanced_mask


    def get_sky_and_ground_masks(self, image: Image.Image) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取天空和地面蒙版

        Args:
            image: PIL 图像 (RGB)

        Returns:
            (天空蒙版, 地面蒙版)，值均为 0-255
        """
        sky_mask = self.segment(image)
        ground_mask = 255 - sky_mask  # 反转蒙版

        return sky_mask, ground_mask



if __name__ == '__main__':
    """测试代码"""
    import rawpy
    from pathlib import Path

    print("=" * 60)
    print("SegFormer 天空分割测试")
    print("=" * 60)

    # 创建检测器
    print("\n1. 初始化 SkyDetector (SegFormer-B0)...")
    detector = SkyDetector(model_size="b0")

    # 测试 RAW 文件
    raw_path_str = "/Users/jameszhenyu/Desktop/Mark Ma/Z9L_8844-2.NEF"
    raw_path = Path(raw_path_str)

    if raw_path.exists():
        print(f"\n2. 正在处理 RAW 文件: {raw_path.name}")
        try:
            # 读取 RAW 文件
            with rawpy.imread(raw_path_str) as raw:
                rgb_image_np = raw.postprocess(use_camera_wb=True, output_bps=8)

            # 转换为 PIL 图像
            image_from_raw = Image.fromarray(rgb_image_np)

            # 进行分割
            print("   正在进行天空分割...")
            sky_mask = detector.segment(image_from_raw)

            # 保存蒙版
            mask_filename = f"sky_mask_segformer_{raw_path.stem}.png"
            Image.fromarray(sky_mask).save(mask_filename)
            print(f"   ✅ 天空蒙版已保存: {mask_filename}")

            # 获取天空和地面蒙版
            print("\n3. 生成天空和地面蒙版...")
            sky_mask, ground_mask = detector.get_sky_and_ground_masks(image_from_raw)

            sky_filename = f"sky_{raw_path.stem}.png"
            ground_filename = f"ground_{raw_path.stem}.png"

            Image.fromarray(sky_mask).save(sky_filename)
            Image.fromarray(ground_mask).save(ground_filename)

            print(f"   ✅ 天空蒙版: {sky_filename}")
            print(f"   ✅ 地面蒙版: {ground_filename}")

            # 统计信息
            sky_pixels = np.sum(sky_mask > 0)
            total_pixels = sky_mask.size
            sky_percentage = (sky_pixels / total_pixels) * 100

            print(f"\n4. 分割统计:")
            print(f"   图像尺寸: {image_from_raw.size[0]} × {image_from_raw.size[1]}")
            print(f"   天空占比: {sky_percentage:.1f}%")
            print(f"   地面占比: {100 - sky_percentage:.1f}%")

            print("\n✅ 测试成功！")

        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n❌ RAW 文件未找到: {raw_path_str}")
        print("   请修改路径后重试")

    print("\n" + "=" * 60)
