"""共享测试 fixtures"""

import sys
import pytest
from pathlib import Path


# ---- Qt 环境（可选） ----

@pytest.fixture(scope="session")
def qapp():
    """整个测试会话共享一个 QApplication（仅 Qt 相关测试需要）"""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


# ---- 文件系统隔离 ----

@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """临时数据目录，mock PathManager 使其指向 tmp_path"""
    from utils.paths import PathManager
    monkeypatch.setattr(PathManager, "COURSES_JSON", tmp_path / "data" / "courses.json")
    monkeypatch.setattr(PathManager, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathManager, "LOG_DIR", tmp_path / "logs")
    yield tmp_path


@pytest.fixture
def tmp_courses_json(tmp_data_dir):
    """创建空 courses.json 并返回其路径"""
    data_dir = tmp_data_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    courses_json = data_dir / "courses.json"
    courses_json.write_text('{"courses": []}', encoding="utf-8")
    return courses_json


# ---- 时间冻结 ----

@pytest.fixture
def frozen_datetime_now(monkeypatch):
    """冻结 datetime.now() 到 2026-06-20 12:00:00"""
    from datetime import datetime

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 6, 20, 12, 0, 0)

    monkeypatch.setattr("models.data_manager.datetime", FrozenDateTime)
    yield FrozenDateTime


@pytest.fixture
def frozen_date_today(monkeypatch):
    """冻结 date.today() 到 2026-06-20"""
    from datetime import date

    class FrozenDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 6, 20)

    monkeypatch.setattr("models.data_manager.date", FrozenDate)
    yield FrozenDate
