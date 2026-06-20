"""测试 app/utils/paths.py"""

from pathlib import Path
from utils.paths import PathManager


class TestPathManager:
    """PathManager 类属性和方法测试"""

    def test_base_dir_is_absolute(self):
        assert PathManager.BASE_DIR.is_absolute()

    def test_base_dir_exists(self):
        assert PathManager.BASE_DIR.exists()

    def test_data_dir_is_sub_of_base(self):
        data = PathManager.DATA_DIR
        assert data.parent == PathManager.BASE_DIR

    def test_log_dir_is_sub_of_base(self):
        log = PathManager.LOG_DIR
        assert log.parent == PathManager.BASE_DIR

    def test_data_dir_name(self):
        assert PathManager.DATA_DIR.name == "data"

    def test_log_dir_name(self):
        assert PathManager.LOG_DIR.name == "logs"

    def test_courses_json_in_data_dir(self):
        assert PathManager.COURSES_JSON.parent == PathManager.DATA_DIR
        assert PathManager.COURSES_JSON.name == "courses.json"

    def test_get_data_file_path(self):
        result = PathManager.get_data_file_path("test.db")
        assert result == PathManager.DATA_DIR / "test.db"

    def test_get_log_file_path(self):
        result = PathManager.get_log_file_path("error.log")
        assert result == PathManager.LOG_DIR / "error.log"

    def test_ensure_dirs_creates_directories(self, monkeypatch, tmp_path):
        """验证 ensure_dirs 在 monkeypatch 路径下创建目录"""
        monkeypatch.setattr(PathManager, "DATA_DIR", tmp_path / "data")
        monkeypatch.setattr(PathManager, "LOG_DIR", tmp_path / "logs")

        assert not (tmp_path / "data").exists()
        assert not (tmp_path / "logs").exists()

        PathManager.ensure_dirs()

        assert (tmp_path / "data").exists()
        assert (tmp_path / "logs").exists()

    def test_ensure_dirs_idempotent(self, monkeypatch, tmp_path):
        """重复调用 ensure_dirs 不应报错"""
        monkeypatch.setattr(PathManager, "DATA_DIR", tmp_path / "data")
        monkeypatch.setattr(PathManager, "LOG_DIR", tmp_path / "logs")

        PathManager.ensure_dirs()  # first call
        PathManager.ensure_dirs()  # second call — should not raise
