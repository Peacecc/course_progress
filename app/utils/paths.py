"""路径管理模块 — 统一管理项目中的各种路径"""

import sys
from pathlib import Path


class PathManager:
    """路径管理类，使用 pathlib 统一管理项目路径"""

    # 项目根目录（app/utils/paths.py → app/utils → app → 项目根）
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    COURSES_JSON = DATA_DIR / "courses.json"
    LOG_DIR = BASE_DIR / "logs"

    @classmethod
    def ensure_dirs(cls):
        """确保必要的目录存在"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_data_file_path(cls, filename: str) -> Path:
        """获取数据目录下的文件路径"""
        return cls.DATA_DIR / filename

    @classmethod
    def get_log_file_path(cls, filename: str) -> Path:
        """获取日志目录下的文件路径"""
        return cls.LOG_DIR / filename
