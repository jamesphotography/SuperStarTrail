"""
日志模块

提供统一的日志功能
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# 全局变量：当前的文件处理器
_file_handler = None
_log_file_path = None


def enable_file_logging(log_dir: Path) -> Path:
    """
    启用文件日志记录，将日志保存到指定目录

    Args:
        log_dir: 日志文件保存目录

    Returns:
        日志文件的完整路径
    """
    global _file_handler, _log_file_path

    # 确保目录存在
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 生成日志文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"SuperStarTrail_{timestamp}.log"
    _log_file_path = log_file

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 创建文件处理器
    _file_handler = logging.FileHandler(log_file, encoding="utf-8")
    _file_handler.setLevel(logging.INFO)
    _file_handler.setFormatter(formatter)

    # 为根日志记录器添加文件处理器（这样所有子日志记录器都会使用它）
    root_logger = logging.getLogger()
    
    # 移除之前的文件处理器（如果有）
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            root_logger.removeHandler(handler)
            handler.close()
    
    root_logger.addHandler(_file_handler)
    root_logger.setLevel(logging.INFO)

    # 记录日志文件创建信息
    root_logger.info(f"日志文件已创建: {log_file}")

    return log_file


def get_log_file_path() -> Path:
    """获取当前日志文件路径"""
    return _log_file_path


def setup_logger(
    name: str = "SuperStarTrail",
    level: int = logging.INFO,
    log_to_file: bool = False,
    log_dir: Path = None,
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_to_file: 是否记录到文件
        log_dir: 日志目录

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_to_file:
        if log_dir is None:
            log_dir = Path.home() / ".superstartrail" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
