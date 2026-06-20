"""测试 app/utils/logger.py"""

import logging
from pathlib import Path

import pytest
from utils.logger import setup_logger


class TestSetupLogger:
    """setup_logger() 测试"""

    def test_returns_logger(self):
        logger = setup_logger("test_logger_1")
        assert isinstance(logger, logging.Logger)

    def test_logger_name_set(self):
        logger = setup_logger("test_logger_2")
        assert logger.name == "test_logger_2"

    def test_console_handler_added(self):
        """无 log_dir 时只创建 StreamHandler"""
        logger = setup_logger("test_logger_3")
        # 至少有一个 console handler
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1

    def test_default_level_is_debug(self):
        logger = setup_logger("test_logger_4")
        assert logger.level == logging.DEBUG

    def test_with_log_dir_creates_file_handler(self, tmp_path):
        log_dir = tmp_path / "logs"
        logger = setup_logger("test_logger_5", log_dir=log_dir)

        assert log_dir.exists()

        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1

    def test_idempotent_no_duplicate_handlers(self):
        """重复调用不重复添加 handler"""
        logger_a = setup_logger("test_logger_6")
        count_a = len(logger_a.handlers)

        logger_b = setup_logger("test_logger_6")
        count_b = len(logger_b.handlers)

        assert count_b == count_a
        assert logger_a is logger_b  # logging.getLogger 返回同一个实例
