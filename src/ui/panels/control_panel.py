"""
处理控制面板
负责开始/停止按钮、进度条和状态显示
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal
from i18n.translator import Translator
from ui.styles import (
    SUCCESS_BUTTON_STYLE,
    DANGER_BUTTON_STYLE,
    COLORS,
)


class ControlPanel(QWidget):
    """处理控制面板"""

    # 信号定义
    start_clicked = pyqtSignal()  # 开始按钮点击
    stop_clicked = pyqtSignal()  # 停止按钮点击

    def __init__(self, translator: Translator, parent=None):
        super().__init__(parent)
        self.tr = translator
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 处理控制（同一行）
        control_layout = QHBoxLayout()

        self.btn_start = QPushButton(self.tr.tr("start"))
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_start.setEnabled(False)
        self.btn_start.setStyleSheet(SUCCESS_BUTTON_STYLE + "padding: 8px 16px; font-size: 13px;")
        control_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton(self.tr.tr("stop"))
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(DANGER_BUTTON_STYLE + "padding: 8px 16px; font-size: 13px;")
        control_layout.addWidget(self.btn_stop)

        # 状态标签
        self.label_status = QLabel(self.tr.tr("ready"))
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setStyleSheet(f"""
            padding: 8px 12px;
            background-color: {COLORS['bg_light']};
            border-radius: 5px;
            color: {COLORS['text_primary']};
            font-size: 11px;
            font-weight: bold;
        """)
        control_layout.addWidget(self.label_status, 1)

        layout.addLayout(control_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%p% (%v/%m)")  # 显示百分比和进度
        layout.addWidget(self.progress_bar)

    def _on_start_clicked(self):
        """开始按钮点击"""
        self.start_clicked.emit()

    def _on_stop_clicked(self):
        """停止按钮点击"""
        self.stop_clicked.emit()

    def set_start_enabled(self, enabled: bool):
        """设置开始按钮是否可用"""
        self.btn_start.setEnabled(enabled)

    def set_stop_enabled(self, enabled: bool):
        """设置停止按钮是否可用"""
        self.btn_stop.setEnabled(enabled)

    def update_status(self, message: str):
        """更新状态标签"""
        self.label_status.setText(message)

    def update_progress(self, current: int, total: int):
        """更新进度条"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def reset_progress(self, total: int = 100):
        """重置进度条"""
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(total)

    def set_processing_state(self):
        """设置为处理中状态"""
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def set_idle_state(self, can_start: bool = False):
        """设置为空闲状态"""
        self.btn_start.setEnabled(can_start)
        self.btn_stop.setEnabled(False)
