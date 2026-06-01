"""
FileListPanel 测试
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QMessageBox

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from i18n.translator import Translator
from ui.panels.file_list_panel import FileListPanel


class _FakeSettings:
    def get_recent_dirs(self):
        return []

    def add_recent_dir(self, _path: str):
        return None


class TestFileListPanel(unittest.TestCase):
    """FileListPanel 行为测试"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_files(self, *names: str):
        for name in names:
            (self.folder / name).touch()

    def _make_panel(self):
        return FileListPanel(Translator("zh_CN"))

    @staticmethod
    def _mock_message_box_choice(choice_text: str):
        def fake_exec(box):
            box._mock_clicked_button = next(
                button for button in box.buttons() if choice_text in button.text()
            )
            return 0

        def fake_clicked(box):
            return getattr(box, "_mock_clicked_button", None)

        return fake_exec, fake_clicked

    def test_choose_raw_keeps_jpg_only_files(self):
        """选择 RAW 时应只替换同名对，JPG-only 文件仍保留"""
        self._create_files("a.cr2", "a.jpg", "b.cr2", "c.jpg")
        fake_exec, fake_clicked = self._mock_message_box_choice("RAW")

        with patch("ui.panels.file_list_panel.get_settings", return_value=_FakeSettings()), patch.object(
            QMessageBox, "exec_", fake_exec
        ), patch.object(
            QMessageBox, "clickedButton", fake_clicked
        ):
            panel = self._make_panel()
            panel._load_folder(str(self.folder))

        self.assertEqual(
            [path.name for path in panel.get_all_files()],
            ["a.cr2", "b.cr2", "c.jpg"],
        )

    def test_choose_jpg_keeps_raw_only_files(self):
        """选择 JPG 时应只替换同名对，RAW-only 文件仍保留"""
        self._create_files("a.cr2", "a.jpg", "b.cr2", "c.jpg")
        fake_exec, fake_clicked = self._mock_message_box_choice("JPG")

        with patch("ui.panels.file_list_panel.get_settings", return_value=_FakeSettings()), patch.object(
            QMessageBox, "exec_", fake_exec
        ), patch.object(
            QMessageBox, "clickedButton", fake_clicked
        ):
            panel = self._make_panel()
            panel._load_folder(str(self.folder))

        self.assertEqual(
            [path.name for path in panel.get_all_files()],
            ["a.jpg", "b.cr2", "c.jpg"],
        )

    def test_load_folder_includes_cr3_and_tiff(self):
        """文件列表应识别 CR3 与 TIFF。"""
        self._create_files("a.CR3", "b.tiff", "c.jpg", "ignore.bmp")

        with patch("ui.panels.file_list_panel.get_settings", return_value=_FakeSettings()):
            panel = self._make_panel()
            panel._load_folder(str(self.folder))

        self.assertEqual(
            [path.name for path in panel.get_all_files()],
            ["a.CR3", "b.tiff", "c.jpg"],
        )

    def test_rotation_change_does_not_emit_first_file_preview(self):
        """旋转改变时不应强制把预览切回第一张"""
        with patch("ui.panels.file_list_panel.get_settings", return_value=_FakeSettings()):
            panel = self._make_panel()
            panel.raw_files = [Path("/tmp/a.cr2"), Path("/tmp/b.cr2")]
            clicked = []
            panel.file_clicked.connect(clicked.append)

            panel._on_rotation_changed(1)

        self.assertEqual(clicked, [])

    def test_mask_feature_disabled(self):
        """蒙版功能临时下线时，UI 应禁用且处理流程拿不到蒙版路径"""
        with patch("ui.panels.file_list_panel.get_settings", return_value=_FakeSettings()):
            panel = self._make_panel()
            panel._mask_path = Path("/tmp/test_mask.png")

        self.assertFalse(panel.btn_select_mask.isEnabled())
        self.assertFalse(panel.btn_clear_mask.isEnabled())
        self.assertEqual(panel.label_mask.text(), "蒙版功能已临时禁用")
        self.assertIsNone(panel.get_mask_path())
