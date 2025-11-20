"""
SuperStarTrail 主程序入口
"""

import sys
import os
from pathlib import Path

# CRITICAL FIX: Remove OpenCV_LOADER before any imports to prevent recursion detection
# This must be the FIRST thing we do, before importing any other modules
if hasattr(sys, 'OpenCV_LOADER'):
    delattr(sys, 'OpenCV_LOADER')

# Fix sys.path for PyInstaller
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    application_path = sys._MEIPASS
else:
    # Running in normal Python environment
    application_path = str(Path(__file__).parent)
    # Only add to sys.path if not frozen (PyInstaller handles this)
    if application_path not in sys.path:
        sys.path.insert(0, application_path)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from ui.main_window import MainWindow
from utils.logger import setup_logger


def main():
    """主函数"""
    # 设置日志
    logger = setup_logger("SuperStarTrail")
    logger.info("启动 SuperStarTrail...")

    # 设置高DPI支持（必须在 QApplication 创建之前）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("SuperStarTrail")
    app.setOrganizationName("SuperStarTrail")

    # 设置应用程序图标
    icon_path = Path(__file__).parent / "resources" / "logo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # 创建主窗口
    window = MainWindow()
    window.show()

    logger.info("SuperStarTrail 启动完成")

    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
