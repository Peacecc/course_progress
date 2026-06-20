"""主控制器 — 应用的核心编排层，负责所有业务逻辑，连接 View 和 Model"""

import logging
from PySide6.QtCore import QObject

from models.data_manager import DataManager
from models.course_stats import CourseCardData, DashboardData
from services.theme_service import ThemeService
from services.player.player_service import VLC_AVAILABLE, VLCPlayerProxy, QtPlayerProxy
from services.scanner import VideoScanner
from utils.paths import PathManager
from utils.logger import setup_logger

logger = setup_logger("MainController", PathManager.LOG_DIR)


class MainController(QObject):
    """主控制器 — 持有所有 Service/Model 引用，View 通过 Controller 获取数据和执行操作"""

    def __init__(self, data_manager: DataManager, theme_service: ThemeService):
        super().__init__()
        self.data_manager = data_manager
        self.theme_service = theme_service
        self._view = None

        logger.info("MainController 初始化完成")

    # ==================== View 绑定 ====================

    def set_view(self, view):
        """绑定主视图，建立信号连接"""
        self._view = view
        self._connect_signals()

    def _connect_signals(self):
        """连接 View 信号到 Controller 逻辑"""
        view = self._view
        view.home_view.course_selected.connect(self._on_course_selected)
        view.detail_view.back_requested.connect(self._on_go_home)
        view.detail_view.progress_updated.connect(self._on_progress_update)

    # ==================== 导航 ====================

    def _on_course_selected(self, course_id: str):
        """用户选择了某门课程 → 进入详情页"""
        course = self.data_manager.get_course_by_id(course_id)
        if course and self._view:
            self._view.detail_view.load_course(course)
            self._view.stack.setCurrentIndex(1)

    def _on_go_home(self):
        """返回首页"""
        if self._view and hasattr(self._view.detail_view, 'player') and self._view.detail_view.player:
            self._view.detail_view.player.stop()
        if self._view:
            self._view.home_view.refresh_list()
            self._view.stack.setCurrentIndex(0)

    def _on_progress_update(self, course_id: str, rel_path: str,
                             watched_duration: float, completed: bool):
        """视频进度更新"""
        self.data_manager.update_video_progress(course_id, rel_path, watched_duration, completed)

    # ==================== 课程管理 ====================

    def add_course(self, folder_path: str,
                    progress_callback=None) -> dict | None:
        """
        扫描并添加课程。

        Args:
            folder_path: 课程文件夹路径
            progress_callback: 扫描进度回调 (current, total)

        Returns:
            新课程数据，或 None（无视频/重复）
        """
        import os

        # 去重检查
        for course in self.data_manager.get_courses():
            if course['path'] == folder_path:
                logger.warning(f"课程已存在: {folder_path}")
                return None

        # 扫描
        videos, stats = VideoScanner.scan_directory(folder_path, progress_callback)

        if stats['total_videos'] == 0:
            logger.warning(f"未找到视频文件: {folder_path}")
            return None

        name = os.path.basename(folder_path)
        course = self.data_manager.add_course(name, folder_path, videos, stats)
        return course

    def delete_course(self, course_id: str):
        """删除课程"""
        self.data_manager.delete_course(course_id)

    def update_course_name(self, course_id: str, new_name: str):
        """更新课程名称"""
        self.data_manager.update_course_name(course_id, new_name)

    def is_course_exists(self, folder_path: str) -> bool:
        """检查路径是否已添加"""
        for course in self.data_manager.get_courses():
            if course['path'] == folder_path:
                return True
        return False

    # ==================== 首页数据 ====================

    def get_course_card_data_list(self) -> list:
        """获取所有课程的卡片展示数据"""
        return self.data_manager.get_course_card_data()

    def get_all_courses(self) -> list:
        """获取所有课程的原始数据"""
        return self.data_manager.get_courses()

    # ==================== 课程看板数据 ====================

    def get_dashboard_data(self, course_id: str) -> DashboardData:
        """获取课程看板数据"""
        return self.data_manager.get_dashboard_data(course_id)

    def get_course_by_id(self, course_id: str) -> dict | None:
        """获取课程原始数据"""
        return self.data_manager.get_course_by_id(course_id)

    # ==================== 学习计划 ====================

    def set_weekly_schedule(self, course_id: str, schedule: list, start_date_iso: str):
        """设置周计划和开始日期"""
        self.data_manager.set_weekly_schedule(course_id, schedule, start_date_iso)

    # ==================== 播放器 ====================

    def create_player(self, video_surface_id: int = None, video_widget=None):
        """创建播放器实例（优先 VLC，回退 Qt）"""
        if VLC_AVAILABLE and video_surface_id:
            return VLCPlayerProxy(video_surface_id)
        return QtPlayerProxy(video_widget)

    @staticmethod
    def is_vlc_available() -> bool:
        """VLC 是否可用"""
        return VLC_AVAILABLE

    # ==================== 主题 ====================

    def toggle_theme(self):
        """切换主题"""
        self.theme_service.toggle_theme()

    def get_theme(self) -> dict:
        """获取当前主题"""
        return self.theme_service.get_theme()
