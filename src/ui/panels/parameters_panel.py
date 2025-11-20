"""
参数设置面板
负责堆栈模式、白平衡、间隔填充和延时视频参数的设置
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QCheckBox
)
from PyQt5.QtCore import pyqtSignal
from i18n.translator import Translator
from core.stacking_engine import StackMode


class ParametersPanel(QWidget):
    """参数设置面板"""

    # 信号定义
    stack_mode_changed = pyqtSignal(int)  # 堆栈模式改变

    def __init__(self, translator: Translator, parent=None):
        super().__init__(parent)
        self.tr = translator
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 参数设置组
        params_group = QGroupBox(self.tr.tr("parameters"))
        params_layout = QVBoxLayout()

        # 堆栈模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel(self.tr.tr("stack_mode")))
        self.combo_stack_mode = QComboBox()
        self.combo_stack_mode.addItems([
            self.tr.tr("mode_lighten"),
            self.tr.tr("mode_comet"),
            self.tr.tr("mode_average"),
            self.tr.tr("mode_darken"),
        ])
        self.combo_stack_mode.setCurrentIndex(0)  # 默认选择传统星轨
        self.combo_stack_mode.currentIndexChanged.connect(self._on_stack_mode_changed)
        mode_layout.addWidget(self.combo_stack_mode, 1)
        params_layout.addLayout(mode_layout)

        # 彗星尾巴长度（仅彗星模式显示）
        tail_layout = QHBoxLayout()
        self.label_comet_tail = QLabel(self.tr.tr("comet_tail"))
        tail_layout.addWidget(self.label_comet_tail)
        self.combo_comet_tail = QComboBox()
        self.combo_comet_tail.addItems([
            self.tr.tr("tail_short"),
            self.tr.tr("tail_medium"),
            self.tr.tr("tail_long")
        ])
        self.combo_comet_tail.setCurrentIndex(1)  # 默认"中"
        self.combo_comet_tail.setToolTip(
            "控制彗星尾巴的长度\n"
            "短: 快速消失，彗星感强\n"
            "中: 适中效果（推荐）\n"
            "长: 慢慢消失"
        )
        tail_layout.addWidget(self.combo_comet_tail, 1)
        params_layout.addLayout(tail_layout)

        # 默认隐藏彗星选项（因为默认模式是传统星轨）
        self.label_comet_tail.hide()
        self.combo_comet_tail.hide()

        # 白平衡选择
        wb_layout = QHBoxLayout()
        wb_layout.addWidget(QLabel(self.tr.tr("white_balance")))
        self.combo_white_balance = QComboBox()
        self.combo_white_balance.addItems([
            self.tr.tr("wb_camera"),
            self.tr.tr("wb_daylight"),
            self.tr.tr("wb_auto")
        ])
        wb_layout.addWidget(self.combo_white_balance, 1)
        params_layout.addLayout(wb_layout)

        # 选项（间隔填充 + 两种延时视频，放在一行）
        options_layout = QHBoxLayout()

        # 间隔填充
        self.check_enable_gap_filling = QCheckBox(self.tr.tr("gap_filling_checked"))
        self.check_enable_gap_filling.setToolTip(
            "填补星点之间的间隔，使星轨更加连续流畅\n"
            "使用形态学算法，3像素间隔（适合大部分场景）\n"
            "性能影响：几乎无（仅在最后应用一次）"
        )
        self.check_enable_gap_filling.setChecked(True)  # 默认启用
        self.check_enable_gap_filling.stateChanged.connect(
            lambda state: self.check_enable_gap_filling.setText(
                self.tr.tr("gap_filling_checked") if state else self.tr.tr("gap_filling")
            )
        )
        options_layout.addWidget(self.check_enable_gap_filling)

        # 星轨延时
        self.check_enable_timelapse = QCheckBox("星轨延时")
        self.check_enable_timelapse.setToolTip(
            "将星轨形成过程制作为延时视频\n"
            "展示从第一张到最后一张的星轨变长过程\n"
            "分辨率: 3840×2160 (4K)\n"
            "帧率: 25 FPS（默认值）\n"
            "100张图片 ≈ 4秒视频\n"
            "额外处理时间：约 1-2 分钟"
        )
        self.check_enable_timelapse.setChecked(True)  # 默认开启
        self.check_enable_timelapse.setText("✅ 星轨延时")  # 设置初始文本
        self.check_enable_timelapse.stateChanged.connect(
            lambda state: self.check_enable_timelapse.setText(
                "✅ 星轨延时" if state else "星轨延时"
            )
        )
        options_layout.addWidget(self.check_enable_timelapse)

        # 银河延时
        self.check_enable_simple_timelapse = QCheckBox("银河延时")
        self.check_enable_simple_timelapse.setToolTip(
            "直接将原始照片合成为延时视频\n"
            "不进行星轨堆栈处理\n"
            "分辨率: 3840×2160 (4K)\n"
            "帧率: 25 FPS（默认值）\n"
            "100张图片 ≈ 4秒视频\n"
            "适合展示银河移动、天空运动、云层变化等"
        )
        self.check_enable_simple_timelapse.setChecked(True)  # 默认开启
        self.check_enable_simple_timelapse.setText("✅ 银河延时")  # 设置初始文本
        self.check_enable_simple_timelapse.stateChanged.connect(
            lambda state: self.check_enable_simple_timelapse.setText(
                "✅ 银河延时" if state else "银河延时"
            )
        )
        options_layout.addWidget(self.check_enable_simple_timelapse)

        options_layout.addStretch()
        params_layout.addLayout(options_layout)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

    def _on_stack_mode_changed(self, index: int):
        """堆栈模式改变时的处理"""
        # 只有彗星模式显示尾巴长度选项
        is_comet_mode = (index == 1)
        self.label_comet_tail.setVisible(is_comet_mode)
        self.combo_comet_tail.setVisible(is_comet_mode)

        # 发射信号
        self.stack_mode_changed.emit(index)

    def get_stack_mode(self) -> StackMode:
        """获取当前选择的堆栈模式"""
        mode_map = {
            0: StackMode.LIGHTEN,
            1: StackMode.COMET,
            2: StackMode.AVERAGE,
            3: StackMode.DARKEN,
        }
        return mode_map[self.combo_stack_mode.currentIndex()]

    def get_white_balance(self) -> str:
        """获取白平衡参数"""
        wb_map = {
            0: "camera",
            1: "daylight",
            2: "auto",
        }
        return wb_map[self.combo_white_balance.currentIndex()]

    def get_comet_fade_factor(self) -> float:
        """获取彗星尾巴衰减因子"""
        fade_map = {
            0: 0.96,  # 短
            1: 0.97,  # 中
            2: 0.98,  # 长
        }
        return fade_map[self.combo_comet_tail.currentIndex()]

    def is_gap_filling_enabled(self) -> bool:
        """是否启用间隔填充"""
        return self.check_enable_gap_filling.isChecked()

    def is_timelapse_enabled(self) -> bool:
        """是否启用星轨延时视频"""
        return self.check_enable_timelapse.isChecked()

    def is_simple_timelapse_enabled(self) -> bool:
        """是否启用普通延时视频"""
        return self.check_enable_simple_timelapse.isChecked()

    def get_raw_params(self) -> dict:
        """获取 RAW 处理参数"""
        return {
            "use_camera_wb": self.get_white_balance() == "camera",
            "use_auto_wb": self.get_white_balance() == "auto",
        }
