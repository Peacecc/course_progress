"""视频扫描器 — 递归扫描目录中的视频文件，获取时长等元数据"""

import os
import logging
from pathlib import Path
from typing import Callable

from tinytag import TinyTag

from utils.paths import PathManager
from utils.logger import setup_logger

logger = setup_logger("VideoScanner", PathManager.LOG_DIR)

# 支持的视频扩展名
VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', '.m4v', '.ts', '.m2ts')


class VideoScanner:
    """视频文件扫描器"""

    @staticmethod
    def get_duration(file_path: str) -> float:
        """
        获取单个视频文件的时长（秒）。

        使用 TinyTag 读取元数据，失败或超时返回 0。
        """
        try:
            tag = TinyTag.get(file_path)
            return tag.duration if tag.duration else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def scan_directory(root_path: str,
                        progress_callback: Callable[[int, int], None] = None) -> tuple:
        """
        递归扫描目录中的视频文件。

        扫描流程：
        1. 先遍历目录统计视频文件总数
        2. 逐个获取时长，通过 progress_callback 报告进度

        Args:
            root_path: 课程根目录路径
            progress_callback: 进度回调 (current, total)，在步骤 2 中调用

        Returns:
            (videos: list, stats: dict)
            videos: [{"rel_path": ..., "abs_path": ..., "duration": ...}]
            stats: {"total_videos": int, "total_duration": float}
        """
        root_path = os.path.abspath(root_path)

        # 步骤 1：收集所有视频文件路径
        video_paths = []
        try:
            for root, dirs, files in os.walk(root_path):
                for f in files:
                    if f.lower().endswith(VIDEO_EXTENSIONS):
                        video_paths.append(os.path.join(root, f))
        except PermissionError as e:
            logger.warning(f"目录访问权限不足: {e}")

        total_count = len(video_paths)
        logger.info(f"扫描 {root_path}: 发现 {total_count} 个视频文件")

        # 步骤 2：逐个获取时长
        videos = []
        total_duration = 0.0

        for idx, abs_path in enumerate(video_paths):
            rel_path = os.path.relpath(abs_path, root_path)
            duration = VideoScanner.get_duration(abs_path)
            videos.append({
                "rel_path": rel_path,
                "abs_path": abs_path,
                "duration": duration,
            })
            total_duration += duration

            if progress_callback:
                progress_callback(idx + 1, total_count)

        stats = {"total_videos": total_count, "total_duration": total_duration}
        logger.info(f"扫描完成: {total_count} 个视频, 总时长 {total_duration:.0f} 秒")
        return videos, stats
