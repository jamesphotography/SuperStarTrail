"""
处理控制面板（v2 — 专业摄影软件风格）
Begin Processing 大按钮 + 极细进度条 + 状态文字
零 Emoji，极简专业
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from i18n.translator import Translator
from ui.styles import (
    SUCCESS_BUTTON_STYLE,
    DANGER_BUTTON_STYLE,
    PROGRESS_BAR_STYLE,
    COLORS,
)


def _hairline():
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {COLORS['border']}; border: none;")
    return sep


class ControlPanel(QWidget):
    """处理控制面板（右侧栏底部固定区域）"""

    start_clicked = pyqtSignal()
    stop_clicked  = pyqtSignal()

    def __init__(self, translator: Translator, parent=None):
        super().__init__(parent)
        self.tr = translator
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        layout.addWidget(_hairline())

        inner = QVBoxLayout()
        inner.setContentsMargins(12, 12, 12, 14)
        inner.setSpacing(8)

        # ── Begin Processing 大按钮 ────────────────────────────────────────────
        self.btn_start = QPushButton("Begin Processing")
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_start.setEnabled(False)
        self.btn_start.setMinimumHeight(44)
        self.btn_start.setStyleSheet(SUCCESS_BUTTON_STYLE)
        inner.addWidget(self.btn_start)

        # ── Cancel 按钮（处理中才显示，默认隐藏） ─────────────────────────────
        self.btn_stop = QPushButton("Cancel")
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setMinimumHeight(36)
        self.btn_stop.setStyleSheet(DANGER_BUTTON_STYLE)
        self.btn_stop.hide()
        inner.addWidget(self.btn_stop)

        # ── 进度条（极细 4px，处理中才有颜色） ───────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("")
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(PROGRESS_BAR_STYLE)
        inner.addWidget(self.progress_bar)

        # ── 状态文字 ──────────────────────────────────────────────────────────
        self.label_status = QLabel("Ready")
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_muted']};
            padding: 0;
        """)
        inner.addWidget(self.label_status)

        layout.addLayout(inner)

    # ── 信号 ──────────────────────────────────────────────────────────────────
    def _on_start_clicked(self):
        self.start_clicked.emit()

    def _on_stop_clicked(self):
        self.stop_clicked.emit()

    # ── 公共接口 ──────────────────────────────────────────────────────────────
    def set_start_enabled(self, enabled: bool):
        self.btn_start.setEnabled(enabled)

    def set_stop_enabled(self, enabled: bool):
        self.btn_stop.setEnabled(enabled)

    def update_status(self, message: str):
        self.label_status.setText(message)

    def update_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def reset_progress(self, total: int = 100):
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(total)

    def set_processing_state(self):
        """切换到处理中：隐藏开始，显示取消"""
        self.btn_start.hide()
        self.btn_stop.show()
        self.btn_stop.setEnabled(True)
        self.label_status.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_secondary']};
            padding: 0;
        """)

    def set_idle_state(self, can_start: bool = False):
        """切换到空闲：显示开始，隐藏取消"""
        self.btn_stop.hide()
        self.btn_start.show()
        self.btn_start.setEnabled(can_start)
        self.label_status.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_muted']};
            padding: 0;
        """)
