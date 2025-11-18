"""
对话框模块

包含关于对话框、设置对话框等
"""

from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QTabWidget,
    QWidget,
    QFormLayout,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from utils.settings import get_settings


class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 彗星星轨")
        self.setFixedWidth(500)
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Logo
        logo_path = Path(__file__).parent.parent / "resources" / "logo.png"
        if logo_path.exists():
            logo_label = QLabel()
            pixmap = QPixmap(str(logo_path)).scaled(
                128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)

        # 应用名称
        name_label = QLabel("<h1>彗星星轨</h1>")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        # 版本信息
        version_label = QLabel("<h3>版本 0.3.0</h3>")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # 描述
        description = QLabel(
            "专业的星轨叠加软件<br>"
            "支持 RAW 格式处理、彗星模式、延时视频生成<br><br>"
            "by James Zhen Yu"
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)

        # 功能列表
        features = QLabel(
            "<b>主要功能：</b><br>"
            "• 支持 RAW 格式（CR2, NEF, ARW 等）<br>"
            "• 彗星尾巴效果模拟<br>"
            "• 星点对齐<br>"
            "• 间隙填充<br>"
            "• 延时视频生成<br>"
            "• 亮度拉伸优化"
        )
        features.setWordWrap(True)
        layout.addWidget(features)

        # 版权信息
        copyright_label = QLabel(
            "<br>Copyright © 2024 James Photography<br>"
            "All rights reserved."
        )
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(copyright_label)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        close_button.setFixedWidth(100)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)


class PreferencesDialog(QDialog):
    """偏好设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("偏好设置")
        self.setFixedSize(550, 400)
        self.settings = get_settings()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 创建选项卡
        tabs = QTabWidget()

        # 常规设置选项卡
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "常规")

        # 帮助选项卡
        help_tab = self.create_help_tab()
        tabs.addTab(help_tab, "帮助")

        layout.addWidget(tabs)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Ok).setText("确定")
        button_box.button(QDialogButtonBox.Cancel).setText("取消")
        layout.addWidget(button_box)

        self.setLayout(layout)

    def create_general_tab(self) -> QWidget:
        """创建常规设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # 语言设置组
        lang_group = QGroupBox("语言 / Language")
        lang_layout = QFormLayout()

        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文 (Simplified Chinese)", "English (英语)"])
        self.language_combo.setEnabled(False)
        self.language_combo.setToolTip("语言切换功能将在未来版本中启用\nLanguage switching will be enabled in future versions")
        lang_layout.addRow("界面语言:", self.language_combo)

        lang_note = QLabel("注：语言切换功能即将推出\nNote: Language switching coming soon")
        lang_note.setStyleSheet("color: #666; font-size: 11px;")
        lang_layout.addRow("", lang_note)

        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)

        # 添加弹性空间
        layout.addStretch()

        # 版本信息
        version_label = QLabel(
            "<i>彗星星轨 v0.3.0<br>"
            "设置保存在: ~/.superstartrail/settings.json</i>"
        )
        version_label.setStyleSheet("color: #888; font-size: 10px;")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        widget.setLayout(layout)
        return widget

    def create_help_tab(self) -> QWidget:
        """创建帮助选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 帮助文本
        help_text = QLabel(
            "<h3>使用说明</h3>"
            "<p><b>1. 选择文件</b><br>"
            "点击「选择图片目录」，选择包含星轨照片的文件夹。<br>"
            "支持格式：RAW (CR2, NEF, ARW, DNG等)、TIFF、JPG、PNG。</p>"

            "<p><b>2. 选择模式</b><br>"
            "• <b>常规星轨</b>：传统的星轨叠加效果<br>"
            "• <b>彗星星轨</b>：创造渐变尾巴，模拟彗星划过天空的效果</p>"

            "<p><b>3. 调整参数</b><br>"
            "• <b>彗星尾巴长度</b>：短/中/长，控制尾巴的渐变长度<br>"
            "• <b>RAW参数</b>：曝光补偿和白平衡调整<br>"
            "• <b>间隙填充</b>：消除由于拍摄间隔产生的星轨断点<br>"
            "• <b>延时视频</b>：生成展示星轨形成过程的 4K 25FPS 视频</p>"

            "<p><b>4. 开始处理</b><br>"
            "点击「开始处理」，等待处理完成。<br>"
            "结果会自动保存到：原片目录/彗星星轨/</p>"

            "<hr>"

            "<p style='color: #666; font-size: 11px;'>"
            "<b>提示：</b><br>"
            "• 推荐使用 RAW 格式以获得最佳画质<br>"
            "• 彗星模式「中」尾巴长度适合大多数场景<br>"
            "• 延时视频会额外增加 1-2 分钟处理时间<br>"
            "• 100 张照片约生成 3-4 秒视频</p>"
        )
        help_text.setWordWrap(True)
        help_text.setTextFormat(Qt.RichText)

        # 滚动区域
        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidget(help_text)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget

    def load_settings(self):
        """从设置加载到界面"""
        # 语言设置
        language = self.settings.get("general", "language", "zh_CN")
        if language == "en_US":
            self.language_combo.setCurrentIndex(1)
        else:
            self.language_combo.setCurrentIndex(0)

    def accept(self):
        """保存设置并关闭"""
        # 语言设置
        language = "zh_CN" if self.language_combo.currentIndex() == 0 else "en_US"
        self.settings.set("general", "language", language)

        # 保存到文件
        self.settings.save_settings()

        # 关闭对话框
        super().accept()
