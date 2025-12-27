import os

class PathManager:
    """路径管理类，统一管理项目中的各种路径"""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    COURSES_JSON = os.path.join(DATA_DIR, "courses.json")
    
    @classmethod
    def ensure_dirs(cls):
        """确保必要的目录存在"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
