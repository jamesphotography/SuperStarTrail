"""
ImageExporter 测试
"""

import unittest
import numpy as np
import sys
from pathlib import Path
import tempfile
import shutil

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.exporter import ImageExporter


class TestImageExporter(unittest.TestCase):
    """ImageExporter 测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp())

        # 创建测试图像
        self.test_image_8bit = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        self.test_image_16bit = np.random.randint(0, 65535, (100, 100, 3), dtype=np.uint16)

    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_apply_stretch(self):
        """测试亮度拉伸"""
        # 创建一个已知分布的图像
        img = np.zeros((100, 100, 3), dtype=np.uint16)
        img[10:20, 10:20] = 1000   # 低值区域
        img[40:60, 40:60] = 30000  # 高值区域

        # 应用拉伸
        stretched = ImageExporter.apply_stretch(img, p_low=1.0, p_high=99.0)

        # 验证结果
        self.assertEqual(stretched.dtype, np.uint16)
        self.assertEqual(stretched.shape, img.shape)

        # 拉伸后应该有更大的动态范围
        self.assertGreater(stretched.max(), img.max() * 0.5)

    def test_save_tiff_16bit(self):
        """测试保存 16-bit TIFF"""
        output_path = self.temp_dir / "test_16bit.tif"

        success = ImageExporter.save_tiff(
            self.test_image_16bit,
            output_path,
            bits=16,
            compression="none",
            apply_stretch=False
        )

        self.assertTrue(success)
        self.assertTrue(output_path.exists())

        # 验证文件大小合理（不为空）
        self.assertGreater(output_path.stat().st_size, 0)

    def test_save_tiff_8bit(self):
        """测试保存 8-bit TIFF"""
        output_path = self.temp_dir / "test_8bit.tif"

        success = ImageExporter.save_tiff(
            self.test_image_16bit,
            output_path,
            bits=8,
            compression="none",
            apply_stretch=False
        )

        self.assertTrue(success)
        self.assertTrue(output_path.exists())

    def test_save_png(self):
        """测试保存 PNG"""
        output_path = self.temp_dir / "test.png"

        success = ImageExporter.save_png(
            self.test_image_16bit,
            output_path,
            compress_level=6
        )

        self.assertTrue(success)
        self.assertTrue(output_path.exists())

    def test_save_jpeg(self):
        """测试保存 JPEG"""
        output_path = self.temp_dir / "test.jpg"

        success = ImageExporter.save_jpeg(
            self.test_image_16bit,
            output_path,
            quality=95
        )

        self.assertTrue(success)
        self.assertTrue(output_path.exists())

    def test_save_auto_tiff(self):
        """测试自动格式检测 - TIFF"""
        output_path = self.temp_dir / "test.tiff"

        success = ImageExporter.save_auto(
            self.test_image_16bit,
            output_path
        )

        self.assertTrue(success)
        self.assertTrue(output_path.exists())

    def test_save_auto_png(self):
        """测试自动格式检测 - PNG"""
        output_path = self.temp_dir / "test.png"

        success = ImageExporter.save_auto(
            self.test_image_16bit,
            output_path
        )

        self.assertTrue(success)
        self.assertTrue(output_path.exists())

    def test_save_auto_jpeg(self):
        """测试自动格式检测 - JPEG"""
        output_path = self.temp_dir / "test.jpeg"

        success = ImageExporter.save_auto(
            self.test_image_16bit,
            output_path,
            quality=90
        )

        self.assertTrue(success)
        self.assertTrue(output_path.exists())

    def test_unsupported_format(self):
        """测试不支持的格式"""
        output_path = self.temp_dir / "test.bmp"

        with self.assertRaises(ValueError):
            ImageExporter.save_auto(
                self.test_image_16bit,
                output_path
            )

    def test_invalid_bits(self):
        """测试无效的位深度"""
        output_path = self.temp_dir / "test.tif"

        # save_tiff会返回False而不是抛出异常
        success = ImageExporter.save_tiff(
            self.test_image_16bit,
            output_path,
            bits=24,  # 不支持的位深度
            apply_stretch=False
        )

        # 应该返回 False 表示保存失败
        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()
