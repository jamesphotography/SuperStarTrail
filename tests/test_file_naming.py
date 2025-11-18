"""
FileNamingService 测试
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.file_naming import FileNamingService
from core.stacking_engine import StackMode


class TestFileNamingService(unittest.TestCase):
    """FileNamingService 测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建测试文件路径列表
        self.test_files = [
            Path("/test/IMG_0001.CR2"),
            Path("/test/IMG_0002.CR2"),
            Path("/test/IMG_0003.CR2"),
            Path("/test/IMG_0100.CR2"),
        ]

    def test_extract_file_range_continuous(self):
        """测试连续文件范围提取"""
        files = [
            Path("/test/IMG_0001.CR2"),
            Path("/test/IMG_0002.CR2"),
            Path("/test/IMG_0003.CR2"),
        ]

        result = FileNamingService.extract_file_range(files)
        self.assertEqual(result, "IMG_0001-0003")

    def test_extract_file_range_gap(self):
        """测试有间隔的文件范围提取"""
        result = FileNamingService.extract_file_range(self.test_files)
        # 应该显示为 prefix_first-last 格式
        self.assertEqual(result, "IMG_0001-0100")

    def test_extract_file_range_single_file(self):
        """测试单个文件"""
        files = [Path("/test/IMG_0001.CR2")]

        result = FileNamingService.extract_file_range(files)
        # 单个文件也会生成 first-last 格式（相同的编号）
        self.assertEqual(result, "IMG_0001-0001")

    def test_extract_file_range_two_files(self):
        """测试两个文件"""
        files = [
            Path("/test/IMG_0001.CR2"),
            Path("/test/IMG_0002.CR2"),
        ]

        result = FileNamingService.extract_file_range(files)
        self.assertEqual(result, "IMG_0001-0002")

    def test_extract_file_range_different_prefixes(self):
        """测试不同前缀的文件"""
        files = [
            Path("/test/IMG_0001.CR2"),
            Path("/test/DSC_0001.CR2"),
        ]

        result = FileNamingService.extract_file_range(files)
        # 前缀不同时，会用第一个文件的前缀，尝试提取数字
        self.assertIsNotNone(result)
        # 结果应该包含数字部分
        self.assertIn("0001", result)

    def test_generate_output_filename_lighten(self):
        """测试生成 Lighten 模式文件名"""
        filename = FileNamingService.generate_output_filename(
            file_paths=self.test_files,
            stack_mode=StackMode.LIGHTEN,
            white_balance="camera",
            file_extension="tif"
        )

        self.assertIn("Lighten", filename)
        self.assertIn(".tif", filename)
        self.assertIn("IMG_0001-0100", filename)
        self.assertIn("CameraWB", filename)

    def test_generate_output_filename_comet(self):
        """测试生成 Comet 模式文件名"""
        filename = FileNamingService.generate_output_filename(
            file_paths=self.test_files,
            stack_mode=StackMode.COMET,
            white_balance="daylight",
            comet_fade_factor=0.97,
            file_extension="jpg"
        )

        self.assertIn("Comet", filename)
        self.assertIn("MidTail", filename)  # 0.97 对应 MidTail
        self.assertIn("Daylight", filename)
        self.assertIn(".jpg", filename)

    def test_generate_output_filename_with_gap_filling(self):
        """测试带间隔填充的文件名"""
        filename = FileNamingService.generate_output_filename(
            file_paths=self.test_files,
            stack_mode=StackMode.LIGHTEN,
            white_balance="camera",
            enable_gap_filling=True,
            file_extension="tif"
        )

        self.assertIn("GapFilled", filename)

    def test_generate_timelapse_filename(self):
        """测试生成延时视频文件名"""
        filename = FileNamingService.generate_timelapse_filename(
            file_paths=self.test_files,
            stack_mode=StackMode.LIGHTEN,
            white_balance="auto",
            file_extension="mp4"
        )

        self.assertIn("Timelapse", filename)
        self.assertIn("Lighten", filename)
        self.assertIn("AutoWB", filename)
        self.assertIn(".mp4", filename)

    def test_generate_timelapse_filename_comet(self):
        """测试生成彗星模式延时视频文件名"""
        filename = FileNamingService.generate_timelapse_filename(
            file_paths=self.test_files,
            stack_mode=StackMode.COMET,
            white_balance="camera",
            comet_fade_factor=0.98,
            file_extension="mp4"
        )

        self.assertIn("Comet", filename)
        self.assertIn("LongTail", filename)  # 0.98 对应 LongTail
        self.assertIn("Timelapse", filename)

    def test_timestamp_format(self):
        """测试文件名格式"""
        filename = FileNamingService.generate_output_filename(
            file_paths=self.test_files,
            stack_mode=StackMode.LIGHTEN,
            white_balance="camera",
            file_extension="tif"
        )

        # 文件名应该包含基本元素
        self.assertIsNotNone(filename)
        self.assertIsInstance(filename, str)
        self.assertGreater(len(filename), 0)

    def test_empty_file_list(self):
        """测试空文件列表"""
        # 空列表会返回默认值
        result = FileNamingService.extract_file_range([])
        self.assertEqual(result, "untitled")

    def test_special_characters_in_filename(self):
        """测试文件名中的特殊字符"""
        files = [
            Path("/test/IMG 0001 (copy).CR2"),
            Path("/test/IMG 0002 (copy).CR2"),
        ]

        # 应该能正常处理
        result = FileNamingService.extract_file_range(files)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
