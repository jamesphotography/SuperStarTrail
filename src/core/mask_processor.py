"""
蒙版处理模块

负责加载 PNG 蒙版文件，并将其转换为归一化的 float32 数组。
白色区域（255）= 天空（sky_result），黑色区域（0）= 地景（fg_result）。

蒙版由用户在 PS 中对着 RAW 源文件制作，方向与原始照片一致（未旋转）。
加载时应用与图像相同的旋转，再 resize 到目标尺寸。

为了避免 PS 导出的软边、以及缩放时产生的宽半透明带导致融合边缘发灰，
这里会把蒙版稳定化为“硬分区 + 窄羽化”的 matte。
"""
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter


class MaskProcessor:
    """PNG 蒙版加载器"""

    _EDGE_FEATHER_PX = 1.5

    @staticmethod
    def _stabilize_mask(mask: np.ndarray) -> np.ndarray:
        """
        将任意灰度蒙版收敛为更适合双轨融合的 matte。

        设计目标：
        - 保留用户对白/黑区域的主体意图
        - 缩窄过宽的半透明过渡带
        - 仅在边界保留很窄的羽化，减少山线/树梢处的发灰和重影
        """
        mask = np.clip(mask.astype(np.float32), 0.0, 1.0)

        # 已经是硬蒙版时不做额外处理
        has_soft_transition = np.any((mask > 0.0) & (mask < 1.0))
        if not has_soft_transition:
            return mask

        # 先收敛成硬分区，再做轻微羽化，避免宽半透明边带造成融合脏边
        hard_mask = (mask >= 0.5).astype(np.float32)
        img = Image.fromarray((hard_mask * 255).astype(np.uint8), mode="L")
        feathered = img.filter(ImageFilter.GaussianBlur(radius=MaskProcessor._EDGE_FEATHER_PX))
        return np.array(feathered, dtype=np.float32) / 255.0

    @staticmethod
    def load(mask_path: Path, target_shape: tuple, rotation: int = 0) -> np.ndarray:
        """
        加载 PNG 蒙版，应用旋转后 resize 到目标尺寸，返回 float32 [0,1] 数组。

        蒙版应与 RAW 源文件方向一致（在 PS 中打开 RAW 制作），
        rotation 需与处理图像时的旋转角度相同，确保蒙版与图像对齐。

        Args:
            mask_path:    蒙版 PNG 文件路径
            target_shape: 目标形状 (height, width)，与旋转后的堆栈图像一致
            rotation:     旋转角度（0/90/180/270），与图像处理保持一致

        Returns:
            float32 数组，形状 (height, width)，值域 [0.0, 1.0]

        Raises:
            FileNotFoundError: 文件不存在
            ValueError:        文件不是 PNG 格式
        """
        mask_path = Path(mask_path)

        if not mask_path.exists():
            raise FileNotFoundError(f"蒙版文件不存在: {mask_path}")

        if mask_path.suffix.lower() != ".png":
            raise ValueError(f"蒙版文件必须是 PNG 格式，当前: {mask_path.suffix}")

        img = Image.open(mask_path).convert("L")  # 转灰度

        # 应用与图像相同的旋转（蒙版从 RAW 源文件制作，方向与原始一致）
        if rotation:
            _rotation_map = {90: 3, 180: 2, 270: 1}
            if rotation not in _rotation_map:
                raise ValueError(f"不支持的旋转角度: {rotation}，有效值为 90、180、270")
            k = _rotation_map[rotation]
            arr = np.rot90(np.array(img), k=k)
            img = Image.fromarray(arr)

        # Resize 到目标尺寸
        target_h, target_w = target_shape
        if img.size != (target_w, target_h):
            # 蒙版缩放优先避免振铃和过宽软边，BILINEAR 比 LANCZOS 更稳
            img = img.resize((target_w, target_h), Image.BILINEAR)

        mask = np.array(img, dtype=np.float32) / 255.0
        return MaskProcessor._stabilize_mask(mask)
