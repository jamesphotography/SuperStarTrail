"""
Settings 模块测试
"""

import unittest
import sys
from pathlib import Path
import json
import tempfile
import shutil

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.settings import Settings


class TestSettings(unittest.TestCase):
    """Settings 测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录用于测试配置文件
        self.temp_dir = Path(tempfile.mkdtemp())

        # 创建测试用的 Settings 实例
        self.settings = Settings()
        # 修改设置文件路径为临时目录
        self.settings.settings_dir = self.temp_dir
        self.settings.settings_file = self.temp_dir / "test_config.json"

    def tearDown(self):
        """测试后清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_default_settings(self):
        """测试默认设置"""
        # 语言
        self.assertEqual(self.settings.get_language(), "zh_CN")

        # 视频 FPS
        self.assertEqual(self.settings.get_video_fps(), 30)

        # 间隔填充方法
        self.assertEqual(self.settings.get_gap_fill_method(), "morphological")

        # 间隔大小
        self.assertEqual(self.settings.get_gap_size(), 3)

    def test_set_language(self):
        """测试设置语言"""
        self.settings.set_language("en_US")
        self.assertEqual(self.settings.get_language(), "en_US")

    def test_set_video_fps(self):
        """测试设置视频帧率"""
        self.settings.set("output", "video_fps", 25)
        self.assertEqual(self.settings.get_video_fps(), 25)

    def test_set_gap_fill_method(self):
        """测试设置间隔填充方法"""
        self.settings.set("gap_filling", "method", "linear")
        self.assertEqual(self.settings.get_gap_fill_method(), "linear")

    def test_set_gap_size(self):
        """测试设置间隔大小"""
        self.settings.set("gap_filling", "gap_size", 5)
        self.assertEqual(self.settings.get_gap_size(), 5)

    def test_save_and_load(self):
        """测试保存和加载配置"""
        # 修改一些设置
        self.settings.set_language("en_US")
        self.settings.set("output", "video_fps", 25)
        self.settings.set("gap_filling", "gap_size", 5)

        # 保存设置
        self.settings.save_settings()

        # 创建新的 Settings 实例
        new_settings = Settings()
        new_settings.settings_dir = self.temp_dir
        new_settings.settings_file = self.temp_dir / "test_config.json"
        new_settings.settings = new_settings._load_settings()

        self.assertEqual(new_settings.get_language(), "en_US")
        self.assertEqual(new_settings.get_video_fps(), 25)
        self.assertEqual(new_settings.get_gap_size(), 5)

    def test_set_method(self):
        """测试通用set方法"""
        # 设置任意值
        self.settings.set("output", "video_fps", 20)
        self.assertEqual(self.settings.get("output", "video_fps"), 20)

        self.settings.set("gap_filling", "gap_size", 7)
        self.assertEqual(self.settings.get("gap_filling", "gap_size"), 7)

    def test_config_file_creation(self):
        """测试配置文件自动创建"""
        # 保存设置以创建配置文件
        self.settings.save_settings()

        # 配置文件应该存在
        self.assertTrue(self.settings.settings_file.exists())

        # 验证文件内容是有效的 JSON
        with open(self.settings.settings_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.assertIsInstance(config, dict)

    def test_corrupted_config_file(self):
        """测试损坏的配置文件"""
        # 写入无效的 JSON
        with open(self.settings.settings_file, 'w') as f:
            f.write("{ invalid json }")

        # 应该能够处理损坏的配置文件（重置为默认值）
        settings = Settings()
        settings.settings_dir = self.temp_dir
        settings.settings_file = self.temp_dir / "test_config.json"
        settings.settings = settings._load_settings()

        # 应该使用默认值
        self.assertEqual(settings.get_language(), "zh_CN")

    def test_preview_settings(self):
        """测试预览设置"""
        # 获取预览设置
        max_size = self.settings.get_preview_max_size()
        self.assertIsInstance(max_size, int)
        self.assertGreater(max_size, 0)

        # 获取更新间隔
        update_interval = self.settings.get_preview_update_interval()
        self.assertIsInstance(update_interval, int)
        self.assertGreater(update_interval, 0)

    def test_percentile_settings(self):
        """测试百分位数设置"""
        p_low, p_high = self.settings.get_preview_percentiles()

        self.assertIsInstance(p_low, (int, float))
        self.assertIsInstance(p_high, (int, float))
        self.assertGreater(p_high, p_low)


if __name__ == "__main__":
    unittest.main()
