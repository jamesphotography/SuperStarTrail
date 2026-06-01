"""
UI 样式定义模块 — Lightroom/Capture One 专业摄影软件风格
零 Emoji，极简专业，深色主题
"""

# ─── 色彩系统 ─────────────────────────────────────────────────────────────────
COLORS = {
    # 背景层次
    "bg_base":       "#0d1117",   # 最深：中央预览区
    "bg_sidebar":    "#161b22",   # 侧边栏底色
    "bg_elevated":   "#1c2333",   # 卡片、输入框
    "bg_hover":      "#21293a",   # Hover 状态
    "bg_selected":   "#0d2137",   # 选中行（蓝色调）

    # 主色 — 冷蓝（操作蓝）
    "primary":       "#2563eb",   # 主按钮、选中强调
    "primary_light": "#3b82f6",   # Hover 状态
    "primary_dim":   "#1d4ed8",   # Press 状态
    "primary_tint":  "#0d2137",   # 选中行背景（极淡蓝）

    # 文字层次
    "text_primary":   "#e2e8f0",  # 主标签
    "text_secondary": "#8b949e",  # 次要文字、描述
    "text_muted":     "#4a5568",  # Section 标题、禁用
    "text_link":      "#3b82f6",  # 文字链接

    # 边框
    "border":         "#21293a",  # 普通分隔
    "border_section": "#1c2333",  # Section 间分隔
    "border_accent":  "#2563eb",  # 选中行左边框

    # 功能色
    "success":   "#16a34a",
    "error":     "#dc2626",
    "warning":   "#ca8a04",

    # Toggle
    "toggle_on":  "#2563eb",
    "toggle_off": "#2d3748",
}

# ─── 全局基底 ─────────────────────────────────────────────────────────────────
MAIN_WINDOW_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['bg_base']};
}}
"""

# ─── QSplitter ────────────────────────────────────────────────────────────────
SPLITTER_STYLE = f"""
QSplitter::handle {{
    background-color: {COLORS['border']};
    width: 1px;
}}
"""

# ─── GroupBox（已不再使用，保留兼容） ──────────────────────────────────────────
GROUP_BOX_STYLE = f"""
QGroupBox {{
    background-color: transparent;
    border: none;
    margin-top: 0px;
    padding: 0px;
    font-size: 10px;
    color: {COLORS['text_muted']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 0px;
    padding: 0;
    color: {COLORS['text_muted']};
}}
"""

# ─── Section 标题（SOURCE / OUTPUT / STACK MODE …） ──────────────────────────
SECTION_LABEL_STYLE = f"""
font-size: 10px;
font-weight: bold;
color: {COLORS['text_muted']};
letter-spacing: 1.5px;
padding: 0px 2px;
"""

# ─── 主按钮（Select Directory） ───────────────────────────────────────────────
PRIMARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {COLORS['primary']};
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 9px 16px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {COLORS['primary_light']};
}}
QPushButton:pressed {{
    background-color: {COLORS['primary_dim']};
}}
QPushButton:disabled {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_muted']};
}}
"""

# ─── Begin Processing 大按钮 ──────────────────────────────────────────────────
SUCCESS_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {COLORS['primary']};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 14px 20px;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background-color: {COLORS['primary_light']};
}}
QPushButton:pressed {{
    background-color: {COLORS['primary_dim']};
}}
QPushButton:disabled {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_muted']};
}}
"""

# ─── Stop 按钮 ────────────────────────────────────────────────────────────────
DANGER_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS['error']};
    border: 1px solid {COLORS['error']};
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: rgba(220, 38, 38, 0.1);
}}
QPushButton:pressed {{
    background-color: rgba(220, 38, 38, 0.2);
}}
QPushButton:disabled {{
    color: {COLORS['text_muted']};
    border-color: {COLORS['bg_elevated']};
}}
"""

# ─── 次要按钮（Open Output / Change） ────────────────────────────────────────
SECONDARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 5px;
    padding: 6px 12px;
    font-size: 12px;
}}
QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
    border-color: {COLORS['text_muted']};
}}
QPushButton:pressed {{
    background-color: {COLORS['bg_elevated']};
}}
QPushButton:disabled {{
    color: {COLORS['text_muted']};
    border-color: {COLORS['border']};
}}
"""

# ─── 文字链接按钮（Recent、Change） ──────────────────────────────────────────
LINK_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS['text_link']};
    border: none;
    padding: 2px 0px;
    font-size: 12px;
    text-align: left;
}}
QPushButton:hover {{
    color: {COLORS['primary_light']};
}}
"""

# ─── 分段控制器（旋转：0° 90° 180° 270°） ────────────────────────────────────
# 统一基础样式
_SEG_BASE = f"""
QPushButton {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 500;
    border-radius: 0px;
    min-width: 44px;
}}
QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}
QPushButton:checked {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
    border-color: {COLORS['primary']};
    font-weight: 600;
}}
"""
SEGMENT_BUTTON_FIRST_STYLE = _SEG_BASE.replace(
    "border-radius: 0px;", "border-radius: 4px 0px 0px 4px;"
)
SEGMENT_BUTTON_STYLE = _SEG_BASE
SEGMENT_BUTTON_LAST_STYLE = _SEG_BASE.replace(
    "border-radius: 0px;", "border-radius: 0px 4px 4px 0px;"
)

# ─── 模式选择行（右侧面板单选行） ──────────────────────────────────────────────
MODE_ROW_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0px;
    padding: 10px 14px;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
}}
QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
}}
QPushButton:checked {{
    background-color: {COLORS['primary_tint']};
    border-left: 3px solid {COLORS['primary']};
    color: #ffffff;
    font-weight: 600;
}}
"""

# ─── ComboBox ─────────────────────────────────────────────────────────────────
COMBO_BOX_STYLE = f"""
QComboBox {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 5px 10px;
    font-size: 12px;
}}
QComboBox:hover {{ border-color: {COLORS['text_muted']}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS['text_secondary']};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['primary']};
    border: 1px solid {COLORS['border']};
}}
"""

# ─── CheckBox（保留兼容） ──────────────────────────────────────────────────────
CHECKBOX_STYLE = f"""
QCheckBox {{
    color: {COLORS['text_primary']};
    font-size: 12px;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border-radius: 3px;
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['bg_elevated']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}
"""

# ─── ProgressBar ──────────────────────────────────────────────────────────────
PROGRESS_BAR_STYLE = f"""
QProgressBar {{
    background-color: {COLORS['bg_elevated']};
    border: none;
    border-radius: 3px;
    max-height: 4px;
    text-align: center;
    color: transparent;
    font-size: 1px;
}}
QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 3px;
}}
"""

# ─── ListWidget ───────────────────────────────────────────────────────────────
LIST_WIDGET_STYLE = f"""
QListWidget {{
    background-color: {COLORS['bg_base']};
    color: {COLORS['text_primary']};
    border: none;
    border-top: 1px solid {COLORS['border']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 2px 0px;
    font-size: 11px;
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}}
QListWidget::item {{
    padding: 3px 8px;
}}
QListWidget::item:alternate {{
    background-color: {COLORS['bg_sidebar']};
}}
QListWidget::item:hover {{
    background-color: {COLORS['bg_hover']};
}}
QListWidget::item:selected {{
    background-color: {COLORS['primary_tint']};
    color: {COLORS['text_primary']};
    border-left: 2px solid {COLORS['primary']};
}}
"""

# ─── Label 样式 ───────────────────────────────────────────────────────────────
TITLE_LABEL_STYLE = f"""
font-size: 14px;
font-weight: 600;
color: {COLORS['text_primary']};
"""

SUBTITLE_LABEL_STYLE = f"""
font-size: 10px;
font-weight: bold;
color: {COLORS['text_muted']};
letter-spacing: 1.5px;
"""

INFO_LABEL_STYLE = f"""
font-size: 11px;
color: {COLORS['text_secondary']};
"""

# ─── 预览区域 ─────────────────────────────────────────────────────────────────
PREVIEW_AREA_STYLE = f"""
border: none;
background: {COLORS['bg_base']};
color: {COLORS['text_secondary']};
font-size: 13px;
border-radius: 0px;
"""

# ─── 日志区域 ─────────────────────────────────────────────────────────────────
LOG_TEXT_STYLE = f"""
background: {COLORS['bg_base']};
color: {COLORS['text_secondary']};
font-family: 'Menlo', 'Monaco', 'Consolas', 'Courier New', monospace;
font-size: 11px;
border: none;
border-top: 1px solid {COLORS['border']};
padding: 8px 12px;
"""

# ─── 状态栏 ───────────────────────────────────────────────────────────────────
STATUS_BAR_STYLE = f"""
QStatusBar {{
    background-color: {COLORS['bg_sidebar']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
    font-size: 11px;
}}
"""

# ─── 滚动条（极细） ──────────────────────────────────────────────────────────
SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['bg_elevated']};
    min-height: 24px;
    border-radius: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_muted']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['bg_elevated']};
    min-width: 24px;
    border-radius: 2px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
"""

# ─── 模式选中时描述文字色（用于 QLabel） ──────────────────────────────────────
MODE_CARD_STYLE = MODE_ROW_STYLE  # 别名，兼容旧引用


def get_complete_stylesheet() -> str:
    """获取完整样式表"""
    return "\n".join([
        MAIN_WINDOW_STYLE,
        GROUP_BOX_STYLE,
        SPLITTER_STYLE,
        COMBO_BOX_STYLE,
        CHECKBOX_STYLE,
        PROGRESS_BAR_STYLE,
        LIST_WIDGET_STYLE,
        STATUS_BAR_STYLE,
        SCROLLBAR_STYLE,
    ])
