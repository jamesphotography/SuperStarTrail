"""
UI 样式定义模块

统一的样式表和主题配置
"""

# 主题配色
COLORS = {
    # 主色调 - 深蓝色星空主题
    "primary": "#1e3a8a",  # 深蓝色
    "primary_light": "#3b82f6",  # 亮蓝色
    "primary_dark": "#1e40af",  # 更深的蓝

    # 辅助色 - 橙色彗星色
    "accent": "#f59e0b",  # 橙色
    "accent_light": "#fbbf24",  # 亮橙

    # 背景色
    "bg_dark": "#0f172a",  # 深色背景
    "bg_medium": "#1e293b",  # 中等背景
    "bg_light": "#334155",  # 亮背景

    # 文字色
    "text_primary": "#f1f5f9",  # 主要文字
    "text_secondary": "#94a3b8",  # 次要文字
    "text_muted": "#64748b",  # 灰色文字

    # 边框
    "border": "#475569",
    "border_light": "#64748b",

    # 成功/错误
    "success": "#10b981",
    "error": "#ef4444",
    "warning": "#f59e0b",
}

# 主窗口样式
MAIN_WINDOW_STYLE = f"""
QMainWindow {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['bg_dark']},
        stop:1 {COLORS['bg_medium']}
    );
}}
"""

# GroupBox 样式
GROUP_BOX_STYLE = f"""
QGroupBox {{
    background-color: {COLORS['bg_medium']};
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 15px;
    font-weight: bold;
    font-size: 13px;
    color: {COLORS['text_primary']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 3px 10px;
    background-color: {COLORS['primary']};
    border-radius: 4px;
    color: {COLORS['text_primary']};
}}
"""

# 主要按钮样式（选择目录、开始处理等）
PRIMARY_BUTTON_STYLE = f"""
QPushButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['primary_light']},
        stop:1 {COLORS['primary']}
    );
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #60a5fa,
        stop:1 {COLORS['primary_light']}
    );
}}

QPushButton:pressed {{
    background: {COLORS['primary_dark']};
}}

QPushButton:disabled {{
    background: {COLORS['bg_light']};
    color: {COLORS['text_muted']};
}}
"""

# 成功按钮样式（开始处理）
SUCCESS_BUTTON_STYLE = f"""
QPushButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['success']},
        stop:1 #059669
    );
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: bold;
}}

QPushButton:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #34d399,
        stop:1 {COLORS['success']}
    );
}}

QPushButton:pressed {{
    background: #047857;
}}

QPushButton:disabled {{
    background: {COLORS['bg_light']};
    color: {COLORS['text_muted']};
}}
"""

# 危险按钮样式（停止）
DANGER_BUTTON_STYLE = f"""
QPushButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['error']},
        stop:1 #dc2626
    );
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: bold;
}}

QPushButton:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #f87171,
        stop:1 {COLORS['error']}
    );
}}

QPushButton:pressed {{
    background: #b91c1c;
}}
"""

# 次要按钮样式
SECONDARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
}}

QPushButton:hover {{
    background-color: {COLORS['border']};
    border-color: {COLORS['border_light']};
}}

QPushButton:pressed {{
    background-color: {COLORS['bg_dark']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_muted']};
    border-color: {COLORS['border']};
}}
"""

# ComboBox 样式
COMBO_BOX_STYLE = f"""
QComboBox {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 5px;
    padding: 6px 12px;
    font-size: 12px;
}}

QComboBox:hover {{
    border-color: {COLORS['primary_light']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['primary']};
    border: 1px solid {COLORS['border']};
}}
"""

# CheckBox 样式
CHECKBOX_STYLE = f"""
QCheckBox {{
    color: {COLORS['text_primary']};
    font-size: 12px;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {COLORS['border']};
    background-color: {COLORS['bg_light']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['primary_light']};
}}

QCheckBox::indicator:checked {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS['primary_light']},
        stop:1 {COLORS['primary']}
    );
    border-color: {COLORS['primary_light']};
    border-width: 2px;
}}

QCheckBox::indicator:checked:after {{
    width: 18px;
    height: 18px;
}}
"""

# ProgressBar 样式
PROGRESS_BAR_STYLE = f"""
QProgressBar {{
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
    border-radius: 5px;
    text-align: center;
    color: {COLORS['text_primary']};
    font-size: 12px;
    font-weight: bold;
}}

QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']},
        stop:0.5 {COLORS['primary_light']},
        stop:1 {COLORS['accent']}
    );
    border-radius: 4px;
}}
"""

# ListWidget 样式
LIST_WIDGET_STYLE = f"""
QListWidget {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 5px;
    padding: 5px;
    font-size: 11px;
}}

QListWidget::item {{
    padding: 5px;
    border-radius: 3px;
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_medium']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_primary']};
}}
"""

# Label 样式
TITLE_LABEL_STYLE = f"""
font-size: 18px;
font-weight: bold;
color: {COLORS['text_primary']};
padding: 10px;
"""

SUBTITLE_LABEL_STYLE = f"""
font-size: 14px;
font-weight: bold;
color: {COLORS['text_secondary']};
padding: 5px;
"""

INFO_LABEL_STYLE = f"""
font-size: 11px;
color: {COLORS['text_secondary']};
padding: 3px;
"""

# 预览区域样式
PREVIEW_AREA_STYLE = f"""
border: 2px solid {COLORS['border']};
background: {COLORS['bg_dark']};
color: {COLORS['text_secondary']};
font-size: 14px;
padding: 20px;
border-radius: 8px;
"""

# 日志区域样式
LOG_TEXT_STYLE = f"""
background: {COLORS['bg_dark']};
color: {COLORS['text_primary']};
font-family: 'Monaco', 'Menlo', 'Consolas', 'Courier New', monospace;
font-size: 11px;
border: 1px solid {COLORS['border']};
border-radius: 5px;
padding: 8px;
"""

# 状态栏样式
STATUS_BAR_STYLE = f"""
QStatusBar {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
    font-size: 11px;
}}
"""

def get_complete_stylesheet() -> str:
    """获取完整的样式表"""
    return "\n".join([
        MAIN_WINDOW_STYLE,
        GROUP_BOX_STYLE,
        COMBO_BOX_STYLE,
        CHECKBOX_STYLE,
        PROGRESS_BAR_STYLE,
        LIST_WIDGET_STYLE,
        STATUS_BAR_STYLE,
    ])
