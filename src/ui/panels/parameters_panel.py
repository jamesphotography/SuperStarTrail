"""
参数设置面板（v2 — 专业摄影软件风格）
堆栈模式：带左边框高亮的单选行
增强选项：iOS Toggle 开关
零 Emoji，极简专业
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QButtonGroup, QSizePolicy, QFrame,
)
from PyQt5.QtCore import pyqtSignal, Qt
from i18n.translator import Translator
from core.stacking_engine import StackMode
from ui.styles import (
    MODE_ROW_STYLE, SECTION_LABEL_STYLE, COMBO_BOX_STYLE, COLORS,
)


# ─── Toggle 开关（iOS 风格） ────────────────────────────────────────────────────
class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, label: str, tooltip: str = "", checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.setFixedHeight(34)

        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        if tooltip:
            self._lbl.setToolTip(tooltip)
        layout.addWidget(self._lbl)
        layout.addStretch()

        self._btn = QPushButton()
        self._btn.setCheckable(True)
        self._btn.setChecked(checked)
        self._btn.setFixedSize(40, 22)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(self._on_click)
        if tooltip:
            self._btn.setToolTip(tooltip)
        self._update_style()
        layout.addWidget(self._btn)

    def _on_click(self, checked: bool):
        self._checked = checked
        self._update_style()
        self.toggled.emit(checked)

    def _update_style(self):
        if self._checked:
            self._btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['toggle_on']};
                    border-radius: 11px;
                    border: none;
                }}
            """)
        else:
            self._btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['toggle_off']};
                    border-radius: 11px;
                    border: none;
                }}
            """)

    def isChecked(self) -> bool:
        return self._btn.isChecked()

    def setChecked(self, checked: bool):
        self._checked = checked
        self._btn.setChecked(checked)
        self._update_style()


# ─── 单选模式行 ────────────────────────────────────────────────────────────────
class ModeRow(QWidget):
    """单个堆栈模式选择行：左边框高亮 + 标题 + 描述"""

    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)

        # 底层按钮（整行可点击）
        self._btn = QPushButton(self)
        self._btn.setCheckable(True)
        self._btn.setStyleSheet(MODE_ROW_STYLE)
        self._btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._btn.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # 覆盖层文字（穿透鼠标事件）
        overlay = QWidget(self)
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        ol = QHBoxLayout(overlay)
        ol.setContentsMargins(16, 0, 14, 0)
        ol.setSpacing(10)

        # 单选圆圈指示器
        self._radio_dot = QLabel()
        self._radio_dot.setFixedSize(14, 14)
        self._update_radio(False)
        ol.addWidget(self._radio_dot)

        # 文字列
        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 500; color: {COLORS['text_primary']};"
            " background: transparent; border: none;"
        )
        self._desc_lbl = QLabel(description)
        self._desc_lbl.setStyleSheet(
            f"font-size: 10px; color: {COLORS['text_secondary']};"
            " background: transparent; border: none;"
        )
        text_col.addWidget(self._title_lbl)
        text_col.addWidget(self._desc_lbl)
        ol.addLayout(text_col)
        ol.addStretch()

        self._overlay = overlay
        self._btn.toggled.connect(self._on_toggle)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._btn.setGeometry(0, 0, w, h)
        self._overlay.setGeometry(0, 0, w, h)

    def _on_toggle(self, checked: bool):
        self._update_radio(checked)
        col = COLORS['text_primary'] if checked else COLORS['text_secondary']
        self._desc_lbl.setStyleSheet(
            f"font-size: 10px; color: {col}; background: transparent; border: none;"
        )

    def _update_radio(self, checked: bool):
        if checked:
            self._radio_dot.setStyleSheet(f"""
                background-color: {COLORS['primary']};
                border-radius: 7px;
                border: 2px solid {COLORS['primary_light']};
            """)
        else:
            self._radio_dot.setStyleSheet(f"""
                background-color: transparent;
                border-radius: 7px;
                border: 2px solid {COLORS['text_muted']};
            """)

    @property
    def button(self) -> QPushButton:
        return self._btn


# ─── 细分隔线 ──────────────────────────────────────────────────────────────────
def _hairline():
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {COLORS['border']}; border: none;")
    return sep


# ─── 参数面板主体 ───────────────────────────────────────────────────────────────
class ParametersPanel(QWidget):
    stack_mode_changed = pyqtSignal(int)

    _MODES = [
        ("Lighten",  "Accumulate brightest pixels, classic star trails",  StackMode.LIGHTEN),
        ("Comet",    "Trailing fade effect, dynamic motion feel",          StackMode.COMET),
        ("Average",  "Multi-frame averaging, noise reduction",             StackMode.AVERAGE),
    ]

    def __init__(self, translator: Translator, parent=None):
        super().__init__(parent)
        self.tr = translator
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # ── STACK MODE 标题 ───────────────────────────────────────────────────
        hdr1 = QLabel("STACK MODE")
        hdr1.setStyleSheet(SECTION_LABEL_STYLE + f" padding: 0 16px 8px 16px;")
        layout.addWidget(hdr1)

        layout.addWidget(_hairline())

        # ── 模式选择行 ────────────────────────────────────────────────────────
        self._mode_btn_group = QButtonGroup(self)
        self._mode_btn_group.setExclusive(True)
        self._mode_rows = []

        for i, (title, desc, _) in enumerate(self._MODES):
            row = ModeRow(title, desc)
            self._mode_btn_group.addButton(row.button, i)
            self._mode_rows.append(row)
            layout.addWidget(row)
            layout.addWidget(_hairline())

        self._mode_rows[0].button.setChecked(True)
        self._mode_btn_group.buttonClicked.connect(self._on_mode_clicked)

        # 彗星尾迹长度（仅彗星模式）
        self._comet_row = QWidget()
        comet_layout = QHBoxLayout(self._comet_row)
        comet_layout.setContentsMargins(16, 6, 16, 6)
        self._comet_label = QLabel("Tail Length")
        self._comet_label.setStyleSheet(f"font-size: 11px; color: {COLORS['text_secondary']};")
        comet_layout.addWidget(self._comet_label)
        from PyQt5.QtWidgets import QComboBox
        self.combo_comet_tail = QComboBox()
        self.combo_comet_tail.addItems([
            self.tr.tr("tail_short"),
            self.tr.tr("tail_medium"),
            self.tr.tr("tail_long"),
        ])
        self.combo_comet_tail.setCurrentIndex(1)
        comet_layout.addWidget(self.combo_comet_tail, 1)
        layout.addWidget(self._comet_row)
        self._comet_row.hide()

        # 地景模式（蒙版用，默认隐藏）
        self._fg_row = QWidget()
        fg_layout = QHBoxLayout(self._fg_row)
        fg_layout.setContentsMargins(16, 6, 16, 6)
        self.label_fg_mode = QLabel("Foreground Mode")
        self.label_fg_mode.setStyleSheet(f"font-size: 11px; color: {COLORS['text_secondary']};")
        fg_layout.addWidget(self.label_fg_mode)
        from PyQt5.QtWidgets import QComboBox as _CB
        self.combo_fg_mode = _CB()
        self.combo_fg_mode.addItems(["Average", "Comet"])
        fg_layout.addWidget(self.combo_fg_mode, 1)
        layout.addWidget(self._fg_row)
        self._fg_row.hide()

        # 空隙
        layout.addSpacing(16)

        # ── ENHANCEMENTS 标题 ─────────────────────────────────────────────────
        layout.addWidget(_hairline())
        hdr2 = QLabel("ENHANCEMENTS")
        hdr2.setStyleSheet(SECTION_LABEL_STYLE + f" padding: 10px 16px 8px 16px;")
        layout.addWidget(hdr2)

        # Toggle 行
        toggle_container = QWidget()
        tl = QVBoxLayout(toggle_container)
        tl.setContentsMargins(16, 4, 16, 4)
        tl.setSpacing(0)

        self._toggle_gap = ToggleSwitch(
            "Gap Fill",
            tooltip="Fill gaps between star points for smoother trails",
            checked=True,
        )
        tl.addWidget(self._toggle_gap)
        tl.addWidget(_hairline())

        self._toggle_trail_timelapse = ToggleSwitch(
            "Star Trail Timelapse",
            tooltip="Render the star trail formation as a 4K timelapse video",
            checked=False,
        )
        tl.addWidget(self._toggle_trail_timelapse)
        tl.addWidget(_hairline())

        self._toggle_milky_timelapse = ToggleSwitch(
            "Milky Way Timelapse",
            tooltip="Compile raw frames into a timelapse without stacking",
            checked=False,
        )
        tl.addWidget(self._toggle_milky_timelapse)
        tl.addWidget(_hairline())

        self._toggle_satellite = ToggleSwitch(
            "Remove Satellites",
            tooltip="Detect and remove satellite/aircraft streaks using Hough transform",
            checked=False,
        )
        tl.addWidget(self._toggle_satellite)

        layout.addWidget(toggle_container)
        layout.addStretch()

    # ── 内部回调 ──────────────────────────────────────────────────────────────
    def _on_mode_clicked(self, btn):
        idx = self._mode_btn_group.id(btn)
        self._comet_row.setVisible(idx == 1)
        self.stack_mode_changed.emit(idx)

    # ── 公共接口 ──────────────────────────────────────────────────────────────
    def get_stack_mode(self) -> StackMode:
        idx = self._mode_btn_group.checkedId()
        return self._MODES[max(idx, 0)][2]

    def get_comet_fade_factor(self) -> float:
        return {0: 0.96, 1: 0.97, 2: 0.98}.get(self.combo_comet_tail.currentIndex(), 0.97)

    def set_fg_mode_visible(self, visible: bool):
        self._fg_row.setVisible(visible)

    def get_fg_mode(self) -> StackMode:
        return StackMode.AVERAGE if self.combo_fg_mode.currentIndex() == 0 else StackMode.COMET

    def is_gap_filling_enabled(self) -> bool:
        return self._toggle_gap.isChecked()

    def is_timelapse_enabled(self) -> bool:
        return self._toggle_trail_timelapse.isChecked()

    def is_simple_timelapse_enabled(self) -> bool:
        return self._toggle_milky_timelapse.isChecked()

    def is_satellite_removal_enabled(self) -> bool:
        return self._toggle_satellite.isChecked()
