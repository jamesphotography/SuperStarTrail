"""
SuperStarTrail 主程序入口
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

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

    # 创建主窗口
    window = MainWindow()
    window.show()

    logger.info("SuperStarTrail 启动完成")

    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
