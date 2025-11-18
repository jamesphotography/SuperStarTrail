"""
批量更新UI翻译的脚本
"""

# 替换映射：旧文本 -> 翻译键
REPLACEMENTS = [
    # 文件选择组
    ('QGroupBox("文件选择")', 'QGroupBox(self.tr.tr("file_list"))'),
    ('QPushButton("📁 选择图片目录")', 'QPushButton(f"📁 {self.tr.tr(\'select_directory\')}")'),
    ('QPushButton("💾 输出目录")', 'QPushButton("💾 " + self.tr.tr("select_directory"))'),
    ('QLabel("默认：原片目录/彗星星轨/")', 'QLabel(self.tr.tr("no_directory_selected"))'),
    ('"已选择 0 个文件"', 'self.tr.tr("no_directory_selected")'),
    ('"已选择 {len(self.raw_files)} 个文件"', 'f"Selected: {len(self.raw_files)} files"'),

    # 参数设置组
    ('QGroupBox("参数设置")', 'QGroupBox(self.tr.tr("parameters"))'),
    ('QLabel("堆栈模式:")', 'QLabel(self.tr.tr("stack_mode"))'),
    ('"Lighten (星轨)"', 'self.tr.tr("mode_lighten")'),
    ('"Comet (彗星)"', 'self.tr.tr("mode_comet")'),
    ('"Average (降噪)"', 'self.tr.tr("mode_average")'),
    ('"Darken (去光污)"', 'self.tr.tr("mode_darken")'),

    # 按钮
    ('"🚀 开始"', 'f"🚀 {self.tr.tr(\'start\')}"'),
    ('"⏹ 停止"', 'f"⏹ {self.tr.tr(\'stop\')}"'),
    ('"✓ 就绪"', 'self.tr.tr("ready")'),
    ('"▶ 播放视频"', 'f"▶ {self.tr.tr(\'play_video\')}"'),
    ('"📂 打开输出目录"', 'f"📂 {self.tr.tr(\'open_output_dir\')}"'),
]

def update_file():
    """更新main_window.py文件"""
    file_path = "src/ui/main_window.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    for old, new in REPLACEMENTS:
        content = content.replace(old, new)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ 已更新 {file_path}")
        print(f"  进行了 {sum(1 for old, _ in REPLACEMENTS if old in original_content)} 处替换")
    else:
        print("没有进行任何替换")

if __name__ == "__main__":
    update_file()
