"""首页视图 — 课程库概览：仪表盘 + 课程卡片网格"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
    QGridLayout, QLabel, QFileDialog, QMessageBox, QProgressDialog,
)
from PySide6.QtCore import Qt, Signal, QThread

from views.widgets.course_card import CourseCard
from views.widgets.home_dashboard import HomeDashboard
from services.theme_service import theme_service
from services.scanner import VideoScanner


class ScanThread(QThread):
    """异步扫描线程"""
    finished = Signal(str, str, list, dict)  # name, path, videos, stats
    progress = Signal(int, int)               # current, total

    def __init__(self, path: str):
        super().__init__()
        self.path = path

    def run(self):
        name = os.path.basename(self.path)
        videos, stats = VideoScanner.scan_directory(
            self.path,
            progress_callback=lambda cur, tot: self.progress.emit(cur, tot)
        )
        self.finished.emit(name, self.path, videos, stats)


class HomeView(QWidget):
    """首页 —— 课程库管理主界面"""

    course_selected = Signal(str)

    def __init__(self, controller, parent=None):
        """
        Args:
            controller: MainController 实例
        """
        super().__init__(parent)
        self.controller = controller

        # ---- 主布局 ----
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        # ---- 顶部仪表盘（4 张汇总统计卡片） ----
        self.dashboard = HomeDashboard()
        main_layout.addWidget(self.dashboard)

        # ---- 工具栏 ----
        toolbar = QHBoxLayout()
        self.label_courses = QLabel("我的课程库")
        toolbar.addWidget(self.label_courses)
        toolbar.addStretch()

        self.add_btn = QPushButton("+ 添加课程")
        self.add_btn.setFixedSize(120, 40)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._add_course)
        toolbar.addWidget(self.add_btn)
        main_layout.addLayout(toolbar)

        # ---- 课程卡片网格 ----
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setSpacing(20)
        for col in range(3):
            self.grid_layout.setColumnStretch(col, 1)

        # 空状态提示
        self.empty_label = QLabel("📂 尚未添加课程\n点击右上角「+ 添加课程」开始")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("font-size: 16px; color: #9aa0a6; margin-top: 100px;")
        self.empty_label.setVisible(False)

        self.scroll_area.setWidget(self.grid_widget)
        main_layout.addWidget(self.scroll_area)
        main_layout.setStretch(0, 2)  # 仪表盘
        main_layout.setStretch(1, 1)  # 工具栏
        main_layout.setStretch(2, 9)  # 课程卡片

        # ---- 主题 ----
        theme_service.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_service.get_theme())

        # ---- 初始加载 ----
        self.refresh_list()

    # ==================== 主题 ====================

    def _apply_theme(self, theme):
        is_dark = theme["name"] == "dark"
        text_color = theme["text_main"]
        accent = theme["accent"]

        self.label_courses.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {text_color}; margin-top: 10px;"
        )
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #1084D9;
            }}
        """)
        self.empty_label.setStyleSheet(
            f"font-size: 16px; color: {theme['text_sec']}; margin-top: 100px;"
        )

    # ==================== 课程操作 ====================

    def _add_course(self):
        """添加课程流程"""
        folder = QFileDialog.getExistingDirectory(self, "选择课程文件夹")
        if not folder:
            return

        # 去重
        if self.controller.is_course_exists(folder):
            QMessageBox.warning(self, "提示", "该课程已添加到列表中")
            return

        # 异步扫描
        self._scan_thread = ScanThread(folder)
        self._scan_thread.finished.connect(self._on_scan_finished)

        # 进度对话框
        self._progress_dialog = QProgressDialog("正在扫描课程视频...", "取消", 0, 0, self)
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.canceled.connect(self._scan_thread.terminate)
        self._scan_thread.finished.connect(self._progress_dialog.close)
        self._scan_thread.progress.connect(
            lambda cur, tot: self._progress_dialog.setLabelText(
                f"正在扫描课程视频... ({cur}/{tot})"
            )
        )
        self._scan_thread.start()

    def _on_scan_finished(self, name: str, path: str, videos: list, stats: dict):
        """扫描完成回调"""
        if stats["total_videos"] == 0:
            QMessageBox.warning(self, "提示", "未在该文件夹中找到视频文件")
            return

        self.controller.data_manager.add_course(name, path, videos, stats)
        self.refresh_list()

    # ==================== 列表刷新 ====================

    def refresh_list(self):
        """刷新课程卡片网格"""
        # 清空旧卡片
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        # 获取数据
        card_data_list = self.controller.get_course_card_data_list()
        courses = self.controller.get_all_courses()

        # 空状态
        if not card_data_list:
            self.empty_label.setVisible(True)
            self.grid_layout.addWidget(self.empty_label, 0, 0)
            self._update_dashboard_empty()
            return

        self.empty_label.setVisible(False)

        # 渲染卡片
        columns = 3
        for idx, card_data in enumerate(card_data_list):
            card = CourseCard()
            card.set_data(card_data)

            # 名称编辑
            card.name_changed.connect(
                lambda new_name, cid=card_data.course_id: self._on_name_changed(cid, new_name)
            )

            # 点击进入详情
            card.clicked.connect(
                lambda checked=False, cid=card_data.course_id: self.course_selected.emit(cid)
            )

            # 删除课程
            card.delete_requested.connect(
                lambda cid=card_data.course_id: self._confirm_delete(cid)
            )

            row = idx // columns
            col = idx % columns
            self.grid_layout.addWidget(card, row, col)

        # 更新仪表盘
        self._update_dashboard(courses)

    def _update_dashboard(self, courses: list):
        """更新首页仪表盘（4 张汇总统计卡片）"""
        total = len(courses)
        if total == 0:
            self._update_dashboard_empty()
            return

        # 聚合所有课程的统计数据
        active = 0
        total_videos = 0
        completed_videos = 0
        today_seconds = 0.0
        today_plan_seconds = 0.0
        streak_days = 0

        from datetime import date
        today_str = date.today().strftime("%Y-%m-%d")

        for course in courses:
            # 进行中
            all_completed = all(v.get("completed", False) for v in course.get("videos", []))
            if not all_completed:
                active += 1

            # 视频进度
            videos = course.get("videos", [])
            total_videos += len(videos)
            completed_videos += sum(1 for v in videos if v.get("completed", False))

            # 今日学习
            daily = course.get("daily_stats", {})
            today_seconds += daily.get(today_str, 0.0)

            # 今日计划
            schedule = course.get("weekly_schedule", [0.0] * 7)
            wd = date.today().weekday()
            if wd < len(schedule):
                today_plan_seconds += schedule[wd] * 3600.0

        # 连续天数（取全部课程的全局 activity_log）
        streak_days = self.controller.data_manager._calculate_streak()

        self.dashboard.update_stats(
            total_courses=total,
            active_courses=active,
            completed_videos=completed_videos,
            total_videos=total_videos,
            today_seconds=today_seconds,
            today_plan_seconds=today_plan_seconds,
            streak_days=streak_days,
        )

    def _update_dashboard_empty(self):
        """空状态仪表盘"""
        self.dashboard.update_stats(0, 0, 0, 0, 0, 0, 0)

    def _on_name_changed(self, course_id: str, new_name: str):
        """课程名称编辑完成"""
        self.controller.update_course_name(course_id, new_name)

    # ==================== 删除课程 ====================

    def _confirm_delete(self, course_id: str):
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除该课程吗？删除后数据不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_course(course_id)
            self.refresh_list()
