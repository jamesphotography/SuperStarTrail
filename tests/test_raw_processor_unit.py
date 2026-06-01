"""
RawProcessor 单元测试
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image
import tifffile
import rawpy

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.raw_processor import RawProcessor


class TestRawProcessorUnit(unittest.TestCase):
    """RawProcessor 的纯单元测试"""

    def test_is_raw_file_only_matches_raw_extensions(self):
        """JPG 不应被识别为 RAW"""
        self.assertTrue(RawProcessor.is_raw_file(Path("test.nef")))
        self.assertFalse(RawProcessor.is_raw_file(Path("test.jpg")))

    def test_is_supported_file_includes_image_formats(self):
        """TIFF/JPG/PNG/CR3 应被识别为支持的格式"""
        self.assertTrue(RawProcessor.is_supported_file(Path("test.tif")))
        self.assertTrue(RawProcessor.is_supported_file(Path("test.jpg")))
        self.assertTrue(RawProcessor.is_supported_file(Path("test.png")))
        self.assertTrue(RawProcessor.is_supported_file(Path("test.CR3")))
        self.assertFalse(RawProcessor.is_supported_file(Path("test.bmp")))

    def test_process_jpg_returns_16bit_array(self):
        """处理 JPG 应返回 16-bit numpy 数组"""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "test.jpg"
            image = np.array(
                [
                    [[255, 128, 0], [0, 64, 255]],
                    [[30, 200, 90], [120, 10, 220]],
                ],
                dtype=np.uint8,
            )
            Image.fromarray(image).save(image_path, "JPEG", quality=100, subsampling=0)

            processor = RawProcessor()
            result = processor.process(image_path)

            self.assertEqual(result.dtype, np.uint16)
            self.assertEqual(result.ndim, 3)
            self.assertEqual(result.shape[2], 3)

    def test_process_jpg_ignores_extra_kwargs(self):
        """process() 应忽略多余的关键字参数（向后兼容）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "test.jpg"
            image = np.zeros((4, 4, 3), dtype=np.uint8)
            Image.fromarray(image).save(image_path)

            processor = RawProcessor()
            # 传入旧版 white_balance / color_temperature 参数不应报错
            result = processor.process(
                image_path,
                white_balance="camera",
                color_temperature=3200,
            )
            self.assertIsNotNone(result)

    def test_process_file_not_found_raises(self):
        """文件不存在时应抛出 FileNotFoundError"""
        processor = RawProcessor()
        with self.assertRaises(FileNotFoundError):
            processor.process(Path("/nonexistent/file.jpg"))

    def test_process_16bit_tiff_preserves_uint16_range(self):
        """16-bit TIFF 应保留 16-bit 动态范围，不应被降到 8-bit。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "test.tiff"
            image = np.array(
                [
                    [[0, 1024, 65535], [4096, 8192, 16384]],
                    [[32768, 50000, 60000], [65535, 12345, 22222]],
                ],
                dtype=np.uint16,
            )
            tifffile.imwrite(image_path, image)

            processor = RawProcessor()
            result = processor.process(image_path)

            self.assertEqual(result.dtype, np.uint16)
            np.testing.assert_array_equal(result, image)

    def test_process_invalid_tiff_raises_value_error(self):
        """损坏的 TIFF 文件应优雅报错，而不是导致崩溃。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "broken.tiff"
            image_path.write_text("not a real tiff", encoding="utf-8")

            processor = RawProcessor()
            with self.assertRaisesRegex(ValueError, "无法读取 TIFF 文件"):
                processor.process(image_path)

    def test_process_unsupported_compressed_raw_returns_friendly_message(self):
        """不支持的专有压缩 RAW 应返回通用型友好提示。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "test.nef"
            image_path.touch()

            processor = RawProcessor()
            with patch(
                "core.raw_processor.rawpy.imread",
                side_effect=rawpy.LibRawFileUnsupportedError("unsupported"),
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "当前版本暂不支持该文件所使用的相机专有压缩 RAW 格式",
                ):
                    processor.process(image_path)


if __name__ == "__main__":
    unittest.main()
