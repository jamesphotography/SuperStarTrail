"""
RAW 图像处理模块

负责读取和处理各种相机的 RAW 格式文件
"""

from utils.logger import setup_logger

logger = setup_logger(__name__)

from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np
import rawpy
import tifffile
from PIL import Image, ImageOps, UnidentifiedImageError


class RawProcessor:
    """RAW 文件处理器 - 支持 RAW、TIFF、JPG 格式"""

    # 支持的 RAW 格式
    SUPPORTED_RAW_FORMATS = {
        ".3fr",
        ".ari",
        ".arw",
        ".bay",
        ".cap",
        ".cr2",
        ".cr3",
        ".crw",
        ".cs1",
        ".dc2",
        ".dcr",
        ".dng",
        ".drf",
        ".eip",
        ".erf",
        ".fff",
        ".gpr",
        ".iiq",
        ".k25",
        ".kdc",
        ".mdc",
        ".mef",
        ".mos",
        ".mrw",
        ".nef",
        ".nrw",
        ".orf",
        ".pef",
        ".ptx",
        ".pxn",
        ".qtk",
        ".r3d",
        ".raf",
        ".raw",
        ".rdc",
        ".rw2",
        ".sr2",
        ".srf",
        ".srw",
        ".x3f",
    }

    TIFF_FORMATS = {".tif", ".tiff"}

    # 支持的其他格式
    SUPPORTED_IMAGE_FORMATS = TIFF_FORMATS | {".jpg", ".jpeg", ".png"}

    # 所有支持的格式
    SUPPORTED_FORMATS = SUPPORTED_RAW_FORMATS | SUPPORTED_IMAGE_FORMATS

    UNSUPPORTED_COMPRESSED_RAW_MESSAGE = (
        "当前版本暂不支持该文件所使用的相机专有压缩 RAW 格式。"
        "常见情况包括 Nikon HE/HE* NEF、Sony 部分 Compressed / Compressed(HQ) / Medium / Small RAW。"
        "建议改用 Lossless Compressed / Uncompressed RAW，或先转换为兼容格式后再导入。"
    )

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
        return file_path.suffix.lower() in RawProcessor.SUPPORTED_RAW_FORMATS

    @staticmethod
    def scan_directory(directory: Path) -> List[Path]:
        """扫描目录内所有支持的图片文件（按名称排序）"""
        return sorted(
            [
                file_path
                for file_path in directory.iterdir()
                if file_path.is_file()
                and not file_path.name.startswith(".")
                and RawProcessor.is_supported_file(file_path)
            ],
            key=lambda file_path: file_path.name.lower(),
        )

    def process(
        self,
        raw_path: Path,
        apply_exif_rotation: bool = False,
        rotation: int = 0,
        **kwargs,
    ) -> np.ndarray:
        """
        处理图像文件并返回 RGB 图像数组
        支持 RAW、TIFF、JPG、PNG 格式

        Args:
            raw_path: 图像文件路径
            apply_exif_rotation: 是否应用 EXIF 旋转（仅预览时使用）
            **kwargs: 忽略的额外参数（向后兼容）

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

        # 如果是 RAW 格式，使用 rawpy 处理（始终使用相机白平衡）
        if suffix in self.SUPPORTED_RAW_FORMATS:
            rgb = self._process_raw(raw_path)
        elif suffix in self.TIFF_FORMATS:
            rgb = self._process_tiff(raw_path, apply_exif_rotation=apply_exif_rotation)
        else:
            rgb = self._process_standard_image(
                raw_path,
                apply_exif_rotation=apply_exif_rotation,
            )

        # 应用手动旋转（顺时针，整批统一）
        if rotation:
            k = {90: 3, 180: 2, 270: 1}[rotation]
            rgb = np.rot90(rgb, k=k)

        return rgb

    def _process_raw(self, raw_path: Path) -> np.ndarray:
        """使用 rawpy 解码 RAW。"""
        params = self.default_params.copy()

        try:
            with rawpy.imread(str(raw_path)) as raw:
                return raw.postprocess(**params)
        except (
            rawpy.LibRawFileUnsupportedError,
            rawpy.NotSupportedError,
        ) as exc:
            raise self._build_unsupported_raw_error(raw_path) from exc
        except (
            rawpy.LibRawError,
            rawpy.LibRawFatalError,
            OSError,
            ValueError,
        ) as exc:
            raise ValueError(f"RAW 解码失败: {raw_path.name} ({exc})") from exc

    @classmethod
    def _build_unsupported_raw_error(cls, raw_path: Path) -> ValueError:
        """构造统一的“专有压缩 RAW 暂不支持”错误。"""
        return ValueError(f"{raw_path.name}: {cls.UNSUPPORTED_COMPRESSED_RAW_MESSAGE}")

    @staticmethod
    def is_unsupported_raw_exception(exc: Exception) -> bool:
        """判断是否为 rawpy/LibRaw 的“不支持格式”异常。"""
        return isinstance(
            exc,
            (
                rawpy.LibRawFileUnsupportedError,
                rawpy.NotSupportedError,
            ),
        )

    def _process_tiff(self, image_path: Path, apply_exif_rotation: bool = False) -> np.ndarray:
        """使用 tifffile 读取 TIFF，避免 PIL 把 16-bit 彩色图错误降到 8-bit。"""
        try:
            image = tifffile.imread(str(image_path))
        except (tifffile.TiffFileError, ValueError, OSError) as exc:
            raise ValueError(f"无法读取 TIFF 文件: {image_path.name} ({exc})") from exc

        rgb = self._normalize_to_rgb_uint16(image, image_path)
        if apply_exif_rotation:
            rgb = self._apply_tiff_orientation(rgb, image_path)
        return rgb

    def _process_standard_image(
        self,
        image_path: Path,
        apply_exif_rotation: bool = False,
    ) -> np.ndarray:
        """读取 JPG/PNG 等标准位图。"""
        try:
            with Image.open(image_path) as img:
                if apply_exif_rotation:
                    img = ImageOps.exif_transpose(img)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                rgb = np.array(img)
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ValueError(f"无法读取图像文件: {image_path.name} ({exc})") from exc

        return self._normalize_to_rgb_uint16(rgb, image_path)

    @staticmethod
    def _normalize_to_rgb_uint16(image: np.ndarray, image_path: Path) -> np.ndarray:
        """统一输出为 `(H, W, 3)` 的 `uint16` RGB。"""
        image = np.asarray(image)
        image = np.squeeze(image)

        if image.ndim == 3 and image.shape[0] in (3, 4) and image.shape[-1] not in (3, 4):
            image = np.moveaxis(image, 0, -1)

        if image.ndim == 2:
            image = np.repeat(image[:, :, np.newaxis], 3, axis=2)
        elif image.ndim == 3 and image.shape[2] == 1:
            image = np.repeat(image, 3, axis=2)
        elif image.ndim == 3 and image.shape[2] >= 3:
            image = image[:, :, :3]
        else:
            raise ValueError(
                f"不支持的图像维度: {image_path.name} -> {image.shape}"
            )

        if image.dtype == np.uint16:
            return image
        if image.dtype == np.uint8:
            return image.astype(np.uint16) * 257
        if np.issubdtype(image.dtype, np.bool_):
            return image.astype(np.uint16) * 65535
        if np.issubdtype(image.dtype, np.integer):
            return np.clip(image, 0, 65535).astype(np.uint16)
        if np.issubdtype(image.dtype, np.floating):
            max_value = float(np.nanmax(image)) if image.size else 0.0
            if max_value <= 1.0:
                image = image * 65535.0
            return np.clip(image, 0, 65535).astype(np.uint16)

        raise ValueError(f"不支持的像素类型: {image_path.name} -> {image.dtype}")

    @staticmethod
    def _apply_tiff_orientation(image: np.ndarray, image_path: Path) -> np.ndarray:
        """尽量应用 TIFF 中常见的 EXIF 方向标记。"""
        try:
            with Image.open(image_path) as img:
                orientation = img.getexif().get(274)
        except Exception:
            return image

        if orientation == 3:
            return np.rot90(image, k=2)
        if orientation == 6:
            return np.rot90(image, k=3)
        if orientation == 8:
            return np.rot90(image, k=1)
        if orientation == 2:
            return np.fliplr(image)
        if orientation == 4:
            return np.flipud(image)

        return image

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
            logger.info(f"获取缩略图失败: {e}")
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
            logger.info(f"读取元数据失败: {e}")

        return metadata


# 示例用法
if __name__ == "__main__":
    processor = RawProcessor()

    # 测试文件检查
    test_file = Path("test.nef")
    logger.info(f"是否为 RAW 文件: {processor.is_raw_file(test_file)}")
