"""
文件列表管理面板（v2 — 专业摄影软件风格）
SOURCE / OUTPUT / ROTATION 三节，零 Emoji，极简专业
"""
import os
from pathlib import Path
from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QFileDialog,
    QMenu, QMessageBox, QButtonGroup, QSizePolicy, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from i18n.translator import Translator
from ui.styles import (
    PRIMARY_BUTTON_STYLE,
    SECONDARY_BUTTON_STYLE,
    LINK_BUTTON_STYLE,
    SECTION_LABEL_STYLE,
    SEGMENT_BUTTON_FIRST_STYLE,
    SEGMENT_BUTTON_STYLE,
    SEGMENT_BUTTON_LAST_STYLE,
    COLORS,
)
from utils.settings import get_settings
from core.raw_processor import RawProcessor


def _hairline():
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {COLORS['border']}; border: none;")
    return sep


class FileListPanel(QWidget):
    """文件列表管理面板（左侧栏）"""

    MASK_FEATURE_ENABLED = False

    files_selected    = pyqtSignal(list)
    output_dir_changed = pyqtSignal(str)
    file_clicked      = pyqtSignal(object)
    open_output_clicked = pyqtSignal()
    rotation_changed  = pyqtSignal(int)
    mask_path_changed = pyqtSignal(object)

    def __init__(self, translator: Translator, parent=None):
        super().__init__(parent)
        self.tr = translator

        self.raw_files: List[Path] = []
        self.excluded_files: set = set()
        self.output_dir: Optional[str] = None
        self._output_dir_is_manual: bool = False
        self._rotation: int = 0
        self._mask_path: Optional[Path] = None

        self._init_ui()

    # ─────────────────────────────────────────────────────────────────────────
    def _init_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setLayout(root)

        # ── App 品牌头部 ──────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")
        hbox = QHBoxLayout(header)
        hbox.setContentsMargins(14, 0, 14, 0)
        hbox.setSpacing(10)

        logo_path = Path(__file__).parent.parent.parent / "resources" / "logo.png"
        if logo_path.exists():
            logo_lbl = QLabel()
            logo_lbl.setPixmap(
                QPixmap(str(logo_path)).scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            hbox.addWidget(logo_lbl)

        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        app_name = QLabel("SuperStarTrail")
        app_name.setStyleSheet(f"""
            font-size: 13px; font-weight: 600;
            color: {COLORS['text_primary']}; background: transparent;
        """)
        sub_name = QLabel("by James Zhen Yu")
        sub_name.setStyleSheet(f"""
            font-size: 10px; color: {COLORS['text_muted']}; background: transparent;
        """)
        name_col.addWidget(app_name)
        name_col.addWidget(sub_name)
        hbox.addLayout(name_col)
        hbox.addStretch()
        root.addWidget(header)
        root.addWidget(_hairline())

        # ── SOURCE 区 ─────────────────────────────────────────────────────────
        src_lbl = QLabel("SOURCE")
        src_lbl.setStyleSheet(SECTION_LABEL_STYLE + " padding: 10px 14px 6px 14px;")
        root.addWidget(src_lbl)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(12, 0, 12, 0)
        btn_row.setSpacing(6)

        self.btn_select_folder = QPushButton("Select Directory")
        self.btn_select_folder.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_select_folder.setToolTip(self.tr.tr('tooltip_select_folder'))
        btn_row.addWidget(self.btn_select_folder, 1)
        root.addLayout(btn_row)

        # Recent 文字链接 + 文件数量
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(14, 4, 14, 6)
        self._recent_btn = QPushButton("Recent  ▾")
        self._recent_btn.setStyleSheet(LINK_BUTTON_STYLE)
        self._recent_btn.setFixedHeight(22)
        self._recent_menu = QMenu(self)
        self._recent_btn.clicked.connect(self._show_recent_menu)
        self._refresh_recent_menu()
        meta_row.addWidget(self._recent_btn)
        meta_row.addStretch()
        self.label_file_count = QLabel("")
        self.label_file_count.setStyleSheet(f"""
            font-size: 10px; color: {COLORS['text_muted']};
            background: {COLORS['bg_elevated']};
            border-radius: 8px; padding: 1px 7px;
        """)
        self.label_file_count.hide()
        meta_row.addWidget(self.label_file_count)
        root.addLayout(meta_row)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.itemClicked.connect(self._on_file_clicked)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        self.file_list.setMinimumHeight(180)
        root.addWidget(self.file_list, 1)

        # Selected / Excluded 统计
        self._stat_lbl = QLabel("")
        self._stat_lbl.setStyleSheet(f"font-size: 10px; color: {COLORS['text_muted']}; padding: 3px 14px;")
        root.addWidget(self._stat_lbl)

        root.addWidget(_hairline())

        # ── OUTPUT 区 ─────────────────────────────────────────────────────────
        out_lbl = QLabel("OUTPUT")
        out_lbl.setStyleSheet(SECTION_LABEL_STYLE + " padding: 10px 14px 6px 14px;")
        root.addWidget(out_lbl)

        path_row = QHBoxLayout()
        path_row.setContentsMargins(14, 0, 14, 6)
        path_row.setSpacing(8)
        self.label_output_dir = QLabel(self.tr.tr("no_output_directory_selected"))
        self.label_output_dir.setStyleSheet(f"""
            font-size: 11px; color: {COLORS['text_secondary']};
            font-family: 'Menlo', 'Monaco', monospace;
        """)
        self.label_output_dir.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.label_output_dir.setWordWrap(False)
        path_row.addWidget(self.label_output_dir, 1)

        self.btn_select_output = QPushButton("Change")
        self.btn_select_output.setStyleSheet(LINK_BUTTON_STYLE)
        self.btn_select_output.setFixedHeight(22)
        self.btn_select_output.clicked.connect(self.select_output_dir)
        path_row.addWidget(self.btn_select_output)
        root.addLayout(path_row)

        self.btn_open_output = QPushButton("Open Output Folder")
        self.btn_open_output.setStyleSheet(
            SECONDARY_BUTTON_STYLE + "margin: 0 12px 8px 12px;"
        )
        self.btn_open_output.clicked.connect(self._on_open_output_clicked)
        self.btn_open_output.setEnabled(False)
        root.addWidget(self.btn_open_output)

        root.addWidget(_hairline())

        # ── ROTATION 区 ───────────────────────────────────────────────────────
        rot_lbl = QLabel("ROTATION")
        rot_lbl.setStyleSheet(SECTION_LABEL_STYLE + " padding: 10px 14px 6px 14px;")
        root.addWidget(rot_lbl)

        seg_row = QHBoxLayout()
        seg_row.setContentsMargins(14, 0, 14, 12)
        seg_row.setSpacing(0)
        self._rot_group = QButtonGroup(self)
        self._rot_group.setExclusive(True)

        for i, (lbl, val) in enumerate([("0°", 0), ("90°", 90), ("180°", 180), ("270°", 270)]):
            btn = QPushButton(lbl)
            btn.setCheckable(True)
            if i == 0:
                btn.setStyleSheet(SEGMENT_BUTTON_FIRST_STYLE)
                btn.setChecked(True)
            elif i == 3:
                btn.setStyleSheet(SEGMENT_BUTTON_LAST_STYLE)
            else:
                btn.setStyleSheet(SEGMENT_BUTTON_STYLE)
            self._rot_group.addButton(btn, val)
            seg_row.addWidget(btn)

        self._rot_group.buttonClicked.connect(self._on_rotation_btn_clicked)
        root.addLayout(seg_row)

        root.addStretch()

    # ─── Recent 菜单 ──────────────────────────────────────────────────────────
    def _show_recent_menu(self):
        self._recent_menu.exec_(
            self._recent_btn.mapToGlobal(self._recent_btn.rect().bottomLeft())
        )

    def _refresh_recent_menu(self):
        self._recent_menu.clear()
        dirs = [d for d in get_settings().get_recent_dirs() if Path(d).exists()]
        if not dirs:
            a = self._recent_menu.addAction("No recent directories")
            a.setEnabled(False)
        else:
            for path in dirs:
                display = Path(path).name or path
                act = self._recent_menu.addAction(display)
                act.setToolTip(path)
                act.triggered.connect(lambda _c, p=path: self._load_folder(p))

    # ─── 文件夹选择 ───────────────────────────────────────────────────────────
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr.tr("select_directory"))
        if folder:
            self._load_folder(folder)

    def _load_folder(self, folder: str):
        folder_path = Path(folder)
        raw_ext = RawProcessor.SUPPORTED_RAW_FORMATS
        jpg_ext = {".jpg", ".jpeg"}
        all_files = RawProcessor.scan_directory(folder_path)

        raw_files  = sorted([f for f in all_files if f.suffix.lower() in raw_ext])
        jpg_files  = sorted([f for f in all_files if f.suffix.lower() in jpg_ext])
        other_files = sorted(
            [f for f in all_files if f.suffix.lower() not in raw_ext and f.suffix.lower() not in jpg_ext],
            key=lambda x: x.name
        )
        raw_stems = {f.stem for f in raw_files}
        jpg_stems = {f.stem for f in jpg_files}
        common = raw_stems & jpg_stems

        if common:
            mb = QMessageBox(self)
            mb.setWindowTitle("Choose Format")
            mb.setText(f"Found {len(common)} files with matching RAW + JPG pairs. Which format should be used?")
            mb.setIcon(QMessageBox.Question)
            btn_raw = mb.addButton("Use RAW", QMessageBox.AcceptRole)
            mb.addButton("Use JPG", QMessageBox.AcceptRole)
            mb.exec_()
            raw_only = [f for f in raw_files if f.stem not in jpg_stems]
            jpg_only = [f for f in jpg_files if f.stem not in raw_stems]
            if mb.clickedButton() == btn_raw:
                files = sorted(raw_files + jpg_only + other_files, key=lambda x: x.name)
            else:
                files = sorted(jpg_files + raw_only + other_files, key=lambda x: x.name)
        else:
            files = sorted(raw_files + jpg_files + other_files, key=lambda x: x.name)

        if not files:
            QMessageBox.warning(self, "No Files Found",
                "No supported image files found in the selected folder (RAW or JPG).")
            return

        self.raw_files = files
        self.excluded_files.clear()
        self.refresh_file_list()

        # 重置旋转
        self._rotation = 0
        for b in self._rot_group.buttons():
            b.blockSignals(True)
            b.setChecked(self._rot_group.id(b) == 0)
            b.blockSignals(False)

        if not self._output_dir_is_manual:
            self.output_dir = str(Path(folder) / "SuperStarTrail")
            self._update_output_label()
            self.output_dir_changed.emit(self.output_dir)

        get_settings().add_recent_dir(str(folder))
        self._refresh_recent_menu()
        self.files_selected.emit(self.get_files_to_process())
        if self.raw_files:
            self.file_clicked.emit(self.raw_files[0])

    # ─── 输出目录 ─────────────────────────────────────────────────────────────
    def select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir or str(Path.home())
        )
        if folder:
            self.output_dir = folder
            self._output_dir_is_manual = True
            self._update_output_label()
            self.output_dir_changed.emit(self.output_dir)

    def _update_output_label(self):
        if self.output_dir:
            p = Path(self.output_dir)
            short = f"…/{p.parent.name}/{p.name}" if len(str(p)) > 28 else str(p)
            self.label_output_dir.setText(short)
        else:
            self.label_output_dir.setText("Not set")

    # ─── 文件列表 ─────────────────────────────────────────────────────────────
    def refresh_file_list(self):
        self.file_list.clear()
        for i, fp in enumerate(self.raw_files):
            text = fp.name if i not in self.excluded_files else f"[excluded]  {fp.name}"
            self.file_list.addItem(text)
        self._update_stat_label()

    def _update_stat_label(self):
        total = len(self.raw_files)
        excl  = len(self.excluded_files)
        valid = total - excl
        if total == 0:
            self._stat_lbl.setText("")
            self.label_file_count.hide()
        else:
            self.label_file_count.setText(f"{total} files")
            self.label_file_count.show()
            if excl > 0:
                self._stat_lbl.setText(f"Selected: {valid}   Excluded: {excl}")
            else:
                self._stat_lbl.setText(f"Selected: {total}")

    # 兼容旧接口
    def update_file_count_label(self):
        self._update_stat_label()

    def show_context_menu(self, pos):
        if not self.raw_files:
            return
        idxs = [item.row() for item in self.file_list.selectedIndexes()]
        if not idxs:
            return
        menu = QMenu(self)
        all_excl = all(i in self.excluded_files for i in idxs)
        if all_excl:
            act = menu.addAction("Include")
            act.triggered.connect(lambda: self.toggle_file_exclusion(idxs, False))
        else:
            act = menu.addAction("Exclude")
            act.triggered.connect(lambda: self.toggle_file_exclusion(idxs, True))
        menu.exec_(self.file_list.viewport().mapToGlobal(pos))

    def toggle_file_exclusion(self, indices, exclude):
        for i in indices:
            if exclude:
                self.excluded_files.add(i)
            else:
                self.excluded_files.discard(i)
        self.refresh_file_list()
        self.files_selected.emit(self.get_files_to_process())

    # ─── 旋转 ─────────────────────────────────────────────────────────────────
    def _on_rotation_btn_clicked(self, btn):
        self._rotation = self._rot_group.id(btn)
        self.rotation_changed.emit(self._rotation)

    # ─── Getters ──────────────────────────────────────────────────────────────
    def get_files_to_process(self) -> List[Path]:
        return [f for i, f in enumerate(self.raw_files) if i not in self.excluded_files]

    def get_all_files(self) -> List[Path]:
        return self.raw_files.copy()

    def get_output_dir(self) -> Optional[str]:
        return self.output_dir

    def get_rotation(self) -> int:
        return self._rotation

    def has_files(self) -> bool:
        return len(self.get_files_to_process()) > 0

    def set_open_output_enabled(self, enabled: bool):
        self.btn_open_output.setEnabled(enabled)

    def _on_open_output_clicked(self):
        self.open_output_clicked.emit()

    def _on_file_clicked(self, item):
        idx = self.file_list.row(item)
        if 0 <= idx < len(self.raw_files):
            self.file_clicked.emit(self.raw_files[idx])

    # ─── 蒙版（保留接口，功能禁用） ──────────────────────────────────────────
    def select_mask(self): pass
    def clear_mask(self): pass
    def get_mask_path(self): return None
