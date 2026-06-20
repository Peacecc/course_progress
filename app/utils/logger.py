"""日志模块 — 统一的日志配置"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "CourseFlow", log_dir: Path = None) -> logging.Logger:
    """
    创建并配置日志记录器。

    Args:
        name: 日志记录器名称
        log_dir: 日志文件目录（可选，不提供则仅控制台输出）

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 控制台 handler（INFO 级别以上）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        '[%(asctime)s] %(levelname)-7s %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # 文件 handler（DEBUG 级别，记录全部日志）
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_filename = log_dir / f"courseflow_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(str(log_filename), encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            '[%(asctime)s] %(levelname)-7s %(name)s.%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)

    return logger
