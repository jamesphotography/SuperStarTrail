"""
预览面板（v2 — 专业摄影软件风格）
- 无顶部标题（标题在左栏）
- 预览区无边框、填满中央空间
- 底部状态栏：文件名 + 像素信息 + 日志折叠按钮
- 日志抽屉：默认折叠，处理时自动展开
"""
import numpy as np
from pathlib import Path
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QApplication, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from i18n.translator import Translator
from ui.styles import (
    PREVIEW_AREA_STYLE,
    LOG_TEXT_STYLE,
    COLORS,
)
from utils.settings import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    from astropy.visualization import ZScaleInterval, AsinhStretch
    _ASTROPY_AVAILABLE = True
except ImportError:
    _ASTROPY_AVAILABLE = False
    logger.warning("astropy 未安装，预览将使用百分位数拉伸作为备用")


class PreviewPanel(QWidget):
    """预览面板（中央大图区 + 底部可折叠日志抽屉）"""

    def __init__(self, translator: Translator, parent=None):
        super().__init__(parent)
        self.tr = translator

        self._preview_cache_valid = False
        self._preview_stretch_cache = None
        self._current_pixmap: Optional[QPixmap] = None
        self._log_expanded = False
        self._current_image_shape: Optional[tuple] = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # ── 预览图（填满，无边框） ─────────────────────────────────────────────
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(PREVIEW_AREA_STYLE)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setMinimumSize(400, 300)

        bg_path = Path(__file__).parent.parent.parent / "resources" / "bg.jpg"
        if bg_path.exists():
            self._current_pixmap = QPixmap(str(bg_path))
            self.preview_label.setPixmap(
                self._current_pixmap.scaled(
                    self.preview_label.minimumSize(),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        else:
            self.preview_label.setText("Select a directory to begin")

        layout.addWidget(self.preview_label, stretch=1)

        # ── 底部状态栏（24px 固定高度） ───────────────────────────────────────
        status_bar = QWidget()
        status_bar.setFixedHeight(26)
        status_bar.setStyleSheet(f"""
            background-color: {COLORS['bg_sidebar']};
            border-top: 1px solid {COLORS['border']};
        """)
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(12, 0, 12, 0)
        sb_layout.setSpacing(16)

        # 文件名
        self._file_label = QLabel("—")
        self._file_label.setStyleSheet(
            f"font-size: 11px; color: {COLORS['text_secondary']};"
            f" font-family: 'Menlo','Monaco',monospace; background: transparent;"
        )
        sb_layout.addWidget(self._file_label)

        # 像素尺寸
        self._dim_label = QLabel("")
        self._dim_label.setStyleSheet(
            f"font-size: 10px; color: {COLORS['text_muted']}; background: transparent;"
        )
        sb_layout.addWidget(self._dim_label)

        sb_layout.addStretch()

        # 日志折叠按钮
        self._log_btn = QPushButton("Processing Log  ›")
        self._log_btn.setFixedHeight(20)
        self._log_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_muted']};
                border: none;
                font-size: 10px;
                font-weight: 500;
                letter-spacing: 0.5px;
                padding: 0 4px;
            }}
            QPushButton:hover {{
                color: {COLORS['text_secondary']};
            }}
        """)
        self._log_btn.clicked.connect(self._toggle_log)
        sb_layout.addWidget(self._log_btn)

        layout.addWidget(status_bar)

        # ── 日志抽屉（默认折叠） ───────────────────────────────────────────────
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(160)
        self.log_text.setStyleSheet(LOG_TEXT_STYLE)
        self.log_text.hide()
        layout.addWidget(self.log_text)

        self._set_default_instructions()

    # ── 日志折叠 ──────────────────────────────────────────────────────────────
    def _toggle_log(self):
        self._log_expanded = not self._log_expanded
        if self._log_expanded:
            self.log_text.show()
            self._log_btn.setText("Processing Log  ›  ▾")
        else:
            self.log_text.hide()
            self._log_btn.setText("Processing Log  ›")

    # ── 图像拉伸 ──────────────────────────────────────────────────────────────
    @staticmethod
    def _stretch_for_preview(image: np.ndarray, settings) -> np.ndarray:
        if _ASTROPY_AVAILABLE:
            try:
                lum = np.mean(image, axis=2).astype(np.float32) if image.ndim == 3 else image.astype(np.float32)
                vmin, vmax = ZScaleInterval().get_limits(lum)
                scale = max(float(vmax - vmin), 1.0)
                img_f = np.clip((image.astype(np.float32) - vmin) / scale, 0.0, 1.0)
                stretched = AsinhStretch(a=0.1)(img_f)
                return (np.clip(stretched, 0.0, 1.0) * 255).astype(np.uint8)
            except Exception as e:
                logger.debug(f"astropy 拉伸失败: {e}")

        p_low, p_high = settings.get_preview_percentiles()
        v_low  = np.percentile(image, p_low)
        v_high = np.percentile(image, p_high)
        scale  = max(float(v_high - v_low), 1.0)
        return np.clip((image.astype(np.float32) - v_low) / scale * 255, 0, 255).astype(np.uint8)

    # ── 预览更新 ──────────────────────────────────────────────────────────────
    def update_preview(self, image: np.ndarray, mask: Optional[np.ndarray] = None):
        import cv2
        settings = get_settings()
        max_size = settings.get_preview_max_size()

        h, w = image.shape[:2]
        self._current_image_shape = (h, w)

        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            image_small = cv2.resize(image, (int(w * scale), int(h * scale)),
                                     interpolation=cv2.INTER_AREA)
        else:
            image_small = image

        if image_small.dtype == np.uint16:
            img_8 = self._stretch_for_preview(image_small, settings)
        else:
            img_8 = image_small.copy()

        if mask is not None:
            ph, pw = img_8.shape[:2]
            m = cv2.resize(mask, (pw, ph), interpolation=cv2.INTER_AREA)
            alpha = (m * 0.45).astype(np.float32)[:, :, np.newaxis]
            tint = np.zeros_like(img_8, dtype=np.float32)
            tint[:, :, 2] = 200
            img_8 = np.clip(img_8.astype(np.float32) * (1 - alpha) + tint * alpha, 0, 255).astype(np.uint8)

        ih, iw, c = img_8.shape
        q_img = QImage(bytes(img_8.tobytes()), iw, ih, c * iw, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self._current_pixmap = pixmap
        self.preview_label.setPixmap(
            pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.preview_label.update()
        QApplication.processEvents()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_pixmap and not self._current_pixmap.isNull():
            self.preview_label.setPixmap(
                self._current_pixmap.scaled(
                    self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )

    # ── 状态栏更新 ────────────────────────────────────────────────────────────
    def set_status_file(self, filename: str):
        self._file_label.setText(filename)
        if self._current_image_shape:
            h, w = self._current_image_shape
            self._dim_label.setText(f"{w:,} × {h:,} px")

    # ── 日志 API ──────────────────────────────────────────────────────────────
    def append_log(self, message: str):
        if not self._log_expanded:
            self._toggle_log()
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def clear_log(self):
        self.log_text.clear()

    def reset_preview_cache(self):
        self._preview_cache_valid = False
        self._preview_stretch_cache = None
        self._current_image_shape = None

    def show_placeholder(self):
        self.preview_label.clear()
        bg_path = Path(__file__).parent.parent.parent / "resources" / "bg.jpg"
        if bg_path.exists():
            self._current_pixmap = QPixmap(str(bg_path))
            self.preview_label.setPixmap(
                self._current_pixmap.scaled(
                    self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        else:
            self._current_pixmap = None
            self.preview_label.setText("Select a directory to begin")

    def _set_default_instructions(self):
        instructions = (
            "Welcome to SuperStarTrail\n\n"
            "Quick Start:\n"
            "  1. Click 'Select Directory' to choose a folder with RAW files\n"
            "  2. Select a stack mode on the right panel (Lighten / Comet / Average)\n"
            "  3. Configure enhancements as needed\n"
            "  4. Click 'Begin Processing' and wait for completion\n"
            "  5. Output folder opens automatically when done"
        )
        self.log_text.setPlainText(instructions)
