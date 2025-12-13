"""
文件列表管理面板
负责文件选择、输出目录选择、文件列表显示和文件排除功能
"""
import os
from pathlib import Path
from typing import List, Callable, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QListWidget, QFileDialog,
    QMenu, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from i18n.translator import Translator
from ui.styles import (
    PRIMARY_BUTTON_STYLE,
    SECONDARY_BUTTON_STYLE,
    INFO_LABEL_STYLE,
)


class FileListPanel(QWidget):
    """文件列表管理面板"""

    # 信号定义
    files_selected = pyqtSignal(list)  # 当文件列表改变时触发
    output_dir_changed = pyqtSignal(str)  # 当输出目录改变时触发
    file_clicked = pyqtSignal(object)  # 当文件被点击时触发（用于预览）
    open_output_clicked = pyqtSignal()  # 打开输出目录按钮点击

    def __init__(self, translator: Translator, parent=None):
        super().__init__(parent)
        self.tr = translator

        # 数据存储
        self.raw_files: List[Path] = []  # 所有 RAW 文件
        self.excluded_files: set = set()  # 被排除的文件索引
        self.output_dir: Optional[str] = None  # 输出目录

        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 文件选择组
        file_group = QGroupBox(self.tr.tr("file_list"))
        file_layout = QVBoxLayout()

        # 文件选择按钮
        self.btn_select_folder = QPushButton(f"📁 {self.tr.tr('select_directory')}")
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_select_folder.setToolTip(self.tr.tr('tooltip_select_folder'))
        self.btn_select_folder.setStyleSheet(PRIMARY_BUTTON_STYLE)
        file_layout.addWidget(self.btn_select_folder)

        # 输出目录选择
        output_dir_layout = QHBoxLayout()
        self.btn_select_output = QPushButton(f"💾 {self.tr.tr('select_directory')}")
        self.btn_select_output.clicked.connect(self.select_output_dir)
        self.btn_select_output.setToolTip(
            self.tr.tr('tooltip_output_dir') if hasattr(self.tr, 'tr') else "Select output directory"
        )
        self.btn_select_output.setStyleSheet(SECONDARY_BUTTON_STYLE)
        output_dir_layout.addWidget(self.btn_select_output)

        self.label_output_dir = QLabel(self.tr.tr("no_directory_selected"))
        self.label_output_dir.setWordWrap(True)
        self.label_output_dir.setStyleSheet(INFO_LABEL_STYLE)
        output_dir_layout.addWidget(self.label_output_dir, 1)

        file_layout.addLayout(output_dir_layout)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.itemClicked.connect(self._on_file_clicked)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        file_layout.addWidget(self.file_list)

        # 文件计数标签
        self.label_file_count = QLabel(self.tr.tr("files_selected").format(count=0))
        self.label_file_count.setStyleSheet(INFO_LABEL_STYLE)
        file_layout.addWidget(self.label_file_count)

        # 打开输出目录按钮（底部）
        self.btn_open_output = QPushButton(f"📂 {self.tr.tr('open_output_dir')}")
        self.btn_open_output.clicked.connect(self._on_open_output_clicked)
        self.btn_open_output.setEnabled(False)
        self.btn_open_output.setStyleSheet(SECONDARY_BUTTON_STYLE + "padding: 8px 16px;")
        file_layout.addWidget(self.btn_open_output)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

    def select_folder(self):
        """选择包含图片文件的文件夹"""
        folder = QFileDialog.getExistingDirectory(self, self.tr.tr("select_directory"))
        if not folder:
            return
        # 查找所有支持的 RAW 文件
        folder_path = Path(folder)
        raw_extensions = {'.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2', '.raf', '.crw', '.cr3'}
        files = sorted([
            f for f in folder_path.iterdir()
            if f.suffix.lower() in raw_extensions
            and not f.name.startswith('.')
        ])

        if not files:
            QMessageBox.warning(
                self,
                self.tr.tr("warning") if hasattr(self.tr, 'tr') else "警告",
                self.tr.tr("no_raw_files") if hasattr(self.tr, 'tr') else "所选文件夹中没有找到 RAW 文件"
            )
            return

        # 更新文件列表
        self.raw_files = files
        self.excluded_files.clear()  # 清空排除列表
        self.refresh_file_list()

        # 如果未设置输出目录，默认使用源文件夹下的 SuperStarTrail 子目录
        if not self.output_dir:
            self.output_dir = str(Path(folder) / "SuperStarTrail")
            self.label_output_dir.setText(self.output_dir)
            self.output_dir_changed.emit(self.output_dir)

        # 发射信号
        self.files_selected.emit(self.get_files_to_process())

        # 自动预览第一张图片
        if self.raw_files:
            self.file_clicked.emit(self.raw_files[0])

    def select_output_dir(self):
        """选择输出目录"""
        folder = QFileDialog.getExistingDirectory(
            self,
            self.tr.tr("select_output_directory") if hasattr(self.tr, 'tr') else "选择输出目录",
            self.output_dir or str(Path.home())
        )

        if folder:
            self.output_dir = folder
            self.label_output_dir.setText(self.output_dir)
            self.output_dir_changed.emit(self.output_dir)

    def refresh_file_list(self):
        """刷新文件列表显示"""
        self.file_list.clear()

        for i, file_path in enumerate(self.raw_files):
            item_text = file_path.name
            if i in self.excluded_files:
                item_text = f"🚫 {item_text}"  # 被排除的文件显示禁止符号
            self.file_list.addItem(item_text)

        self.update_file_count_label()

    def update_file_count_label(self):
        """更新文件计数标签"""
        total_files = len(self.raw_files)
        excluded_count = len(self.excluded_files)
        valid_count = total_files - excluded_count

        if excluded_count > 0:
            count_text = self.tr.tr("files_selected_with_excluded").format(
                count=valid_count,
                total=total_files,
                excluded=excluded_count
            ) if hasattr(self.tr, 'tr') else f"已选择 {valid_count}/{total_files} 个文件（{excluded_count} 个已排除）"
        else:
            count_text = self.tr.tr("files_selected").format(count=valid_count)

        self.label_file_count.setText(count_text)

    def show_context_menu(self, position):
        """显示文件列表右键菜单"""
        if not self.raw_files:
            return

        selected_indices = [item.row() for item in self.file_list.selectedIndexes()]
        if not selected_indices:
            return

        menu = QMenu(self)

        # 检查选中的文件是否都已被排除
        all_excluded = all(i in self.excluded_files for i in selected_indices)

        if all_excluded:
            # 如果已排除，显示"取消排除"
            action = menu.addAction(
                self.tr.tr("include_files") if hasattr(self.tr, 'tr') else "取消排除"
            )
            action.triggered.connect(lambda: self.toggle_file_exclusion(selected_indices, False))
        else:
            # 显示"排除"
            action = menu.addAction(
                self.tr.tr("exclude_files") if hasattr(self.tr, 'tr') else "排除"
            )
            action.triggered.connect(lambda: self.toggle_file_exclusion(selected_indices, True))

        menu.exec_(self.file_list.viewport().mapToGlobal(position))

    def toggle_file_exclusion(self, indices: List[int], exclude: bool):
        """切换文件的排除状态"""
        for i in indices:
            if exclude:
                self.excluded_files.add(i)
            else:
                self.excluded_files.discard(i)

        self.refresh_file_list()

        # 发射信号通知文件列表已更改
        self.files_selected.emit(self.get_files_to_process())

    def get_files_to_process(self) -> List[Path]:
        """获取需要处理的文件列表（排除已被排除的文件）"""
        return [
            file for i, file in enumerate(self.raw_files)
            if i not in self.excluded_files
        ]

    def get_all_files(self) -> List[Path]:
        """获取所有文件列表（包括已被排除的）"""
        return self.raw_files.copy()

    def get_output_dir(self) -> Optional[str]:
        """获取输出目录"""
        return self.output_dir

    def has_files(self) -> bool:
        """检查是否有可处理的文件"""
        return len(self.get_files_to_process()) > 0

    def set_open_output_enabled(self, enabled: bool):
        """设置打开输出目录按钮是否可用"""
        self.btn_open_output.setEnabled(enabled)

    def _on_open_output_clicked(self):
        """打开输出目录按钮点击"""
        self.open_output_clicked.emit()

    def _on_file_clicked(self, item):
        """文件列表项被点击"""
        # 获取点击的文件索引
        index = self.file_list.row(item)
        if 0 <= index < len(self.raw_files):
            # 发射信号，传递文件路径
            self.file_clicked.emit(self.raw_files[index])
