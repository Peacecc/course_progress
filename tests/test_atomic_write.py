"""测试 app/utils/atomic_write.py — 文件 I/O，使用 tmp_path"""

import json
from pathlib import Path

import pytest
from utils.atomic_write import atomic_write_json, safe_read_json


class TestAtomicWriteAndRead:
    """原子写入 + 安全读取 往返测试"""

    def test_write_and_read_roundtrip(self, tmp_path):
        filepath = tmp_path / "test.json"
        data = {"key": "value", "nested": [1, 2, 3]}
        atomic_write_json(filepath, data)
        result = safe_read_json(filepath)
        assert result == data

    def test_write_and_read_empty(self, tmp_path):
        filepath = tmp_path / "empty.json"
        atomic_write_json(filepath, {})
        assert safe_read_json(filepath) == {}

    def test_write_and_read_list(self, tmp_path):
        filepath = tmp_path / "list.json"
        atomic_write_json(filepath, [1, 2, 3])
        assert safe_read_json(filepath) == [1, 2, 3]

    def test_write_unicode(self, tmp_path):
        filepath = tmp_path / "unicode.json"
        data = {"name": "机器学习", "emoji": "🚀"}
        atomic_write_json(filepath, data, ensure_ascii=False)
        result = safe_read_json(filepath)
        assert result == data

    def test_overwrite(self, tmp_path):
        filepath = tmp_path / "overwrite.json"
        atomic_write_json(filepath, {"version": 1})
        atomic_write_json(filepath, {"version": 2})
        result = safe_read_json(filepath)
        assert result == {"version": 2}

    def test_creates_parent_dirs(self, tmp_path):
        filepath = tmp_path / "deep" / "nested" / "dir" / "data.json"
        assert not filepath.parent.exists()
        atomic_write_json(filepath, {"created": True})
        assert filepath.parent.exists()
        assert safe_read_json(filepath) == {"created": True}


class TestSafeReadJson:
    """safe_read_json 边界情况"""

    def test_nonexistent_file_returns_default(self, tmp_path):
        filepath = tmp_path / "does_not_exist.json"
        result = safe_read_json(filepath, default={"fallback": True})
        assert result == {"fallback": True}

    def test_nonexistent_file_default_default(self, tmp_path):
        """未提供 default 参数时返回 {}"""
        filepath = tmp_path / "nonexistent.json"
        result = safe_read_json(filepath)
        assert result == {}

    def test_corrupt_json_returns_default_and_backs_up(self, tmp_path):
        filepath = tmp_path / "corrupt.json"
        filepath.write_text("this is not valid json {{{", encoding="utf-8")

        result = safe_read_json(filepath, default={"recovered": True})
        assert result == {"recovered": True}

        # 应生成 .bak 备份文件
        bak = tmp_path / "corrupt.json.bak"
        assert bak.exists()
        assert bak.read_text(encoding="utf-8") == "this is not valid json {{{"

    def test_corrupt_json_backup_contains_original(self, tmp_path):
        filepath = tmp_path / "bad.json"
        original = '{"broken": true'
        filepath.write_text(original, encoding="utf-8")

        safe_read_json(filepath, default={})
        bak = tmp_path / "bad.json.bak"
        assert bak.read_text(encoding="utf-8") == original

    def test_empty_file_returns_default(self, tmp_path):
        filepath = tmp_path / "empty.json"
        filepath.write_text("", encoding="utf-8")
        result = safe_read_json(filepath, default=[])
        assert result == []
