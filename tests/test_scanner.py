"""测试 app/services/scanner.py — 需要 mock 文件系统和 TinyTag"""

import os
import pytest
from services.scanner import VideoScanner, VIDEO_EXTENSIONS


class TestVideoExtensions:
    """VIDEO_EXTENSIONS 常量测试"""

    def test_is_tuple(self):
        assert isinstance(VIDEO_EXTENSIONS, tuple)

    def test_contains_mp4(self):
        assert ".mp4" in VIDEO_EXTENSIONS

    def test_contains_common_formats(self):
        common = {".mp4", ".mkv", ".avi", ".mov"}
        assert common.issubset(set(VIDEO_EXTENSIONS))

    def test_all_lowercase(self):
        for ext in VIDEO_EXTENSIONS:
            assert ext == ext.lower()

    def test_all_start_with_dot(self):
        for ext in VIDEO_EXTENSIONS:
            assert ext.startswith(".")


class TestScanDirectory:
    """scan_directory() 测试"""

    def test_scan_empty_directory(self, tmp_path):
        """空目录返回空列表和 0 统计"""
        videos, stats = VideoScanner.scan_directory(str(tmp_path))
        assert videos == []
        assert stats == {"total_videos": 0, "total_duration": 0}

    def test_scan_no_video_files(self, tmp_path):
        """目录中有非视频文件时应忽略"""
        (tmp_path / "readme.txt").write_text("hello")
        (tmp_path / "notes.md").write_text("world")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "image.jpg").write_text("fake")

        videos, stats = VideoScanner.scan_directory(str(tmp_path))
        assert videos == []
        assert stats["total_videos"] == 0

    def test_scan_finds_video_files(self, tmp_path, mocker):
        """找到视频文件，mock TinyTag 返回已知时长"""
        # 创建假视频文件
        (tmp_path / "lesson1.mp4").write_text("fake video content")
        (tmp_path / "lesson2.mkv").write_text("fake video content")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "lesson3.avi").write_text("fake video content")

        # Mock TinyTag.get 返回固定时长
        durations = {"lesson1.mp4": 120.0, "lesson2.mkv": 240.0, "lesson3.avi": 360.0}

        def mock_get(path):
            import os
            from unittest.mock import MagicMock
            tag = MagicMock()
            fname = os.path.basename(path)
            tag.duration = durations.get(fname, 0.0)
            return tag

        mocker.patch("tinytag.TinyTag.get", side_effect=mock_get)

        videos, stats = VideoScanner.scan_directory(str(tmp_path))

        assert stats["total_videos"] == 3
        assert stats["total_duration"] == pytest.approx(720.0)  # 120+240+360
        assert len(videos) == 3

        # 验证 rel_path 字段
        rel_paths = {v["rel_path"] for v in videos}
        assert "lesson1.mp4" in rel_paths
        assert os.path.join("sub", "lesson3.avi").replace("\\", "/") in [
            p.replace("\\", "/") for p in rel_paths
        ]

    def test_scan_progress_callback(self, tmp_path, mocker):
        """验证 progress_callback 被调用且参数正确"""
        (tmp_path / "a.mp4").write_text("x")
        (tmp_path / "b.mp4").write_text("x")
        (tmp_path / "c.mp4").write_text("x")

        # Mock TinyTag
        mock_tag = mocker.MagicMock()
        mock_tag.duration = 60.0
        mocker.patch("tinytag.TinyTag.get", return_value=mock_tag)

        progress_calls = []
        def cb(current, total):
            progress_calls.append((current, total))

        VideoScanner.scan_directory(str(tmp_path), progress_callback=cb)

        assert len(progress_calls) == 3
        # 第一次调用: current=1, total=3
        assert progress_calls[0] == (1, 3)
        # 最后一次调用: current=3, total=3
        assert progress_calls[-1] == (3, 3)

    def test_scan_permission_error_handled(self, tmp_path, mocker):
        """PermissionError 被捕获，返回已收集的视频"""
        # Mock os.walk 让它对第一层正常但进入子目录时抛异常
        original_walk = __import__("os").walk

        def mock_walk(path):
            yield str(tmp_path), [], ["a.mp4"]
            raise PermissionError("Access denied")

        mocker.patch("os.walk", side_effect=mock_walk)
        mocker.patch("tinytag.TinyTag.get", return_value=mocker.MagicMock(duration=60.0))

        videos, stats = VideoScanner.scan_directory(str(tmp_path))
        # 应至少收集到 a.mp4
        assert stats["total_videos"] >= 1
