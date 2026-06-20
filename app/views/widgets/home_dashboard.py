"""首页仪表盘组件 — 4 张汇总统计卡片，全局学习状态一目了然"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from services.theme_service import theme_service
from utils.fonts import get_font


class StatCard(QWidget):
    """单张统计卡片"""

    def __init__(self, icon: str, title: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(118)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(6)

        # 图标 + 标题行
        header = QHBoxLayout()
        header.setSpacing(8)

        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 16))
        header.addWidget(self.icon_label)

        self.title_label = QLabel(title)
        self.title_label.setFont(get_font("Regular", 11))
        header.addWidget(self.title_label)
        header.addStretch()

        layout.addLayout(header)

        # 主要数值
        self.value_label = QLabel("--")
        self.value_label.setFont(get_font("Bold", 22))
        layout.addWidget(self.value_label)

        # 副文字
        self.sub_label = QLabel("")
        self.sub_label.setFont(get_font("Regular", 10))
        self.sub_label.setWordWrap(True)
        layout.addWidget(self.sub_label)

        # 进度条（部分卡片使用）
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        theme_service.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_service.get_theme())

    def _apply_theme(self, theme):
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {theme['bg_sec']};
                border: 1px solid {theme['border']};
                border-radius: 12px;
            }}
        """)
        self.title_label.setStyleSheet(
            f"color: {theme['text_sec']}; background: transparent; border: none;"
        )
        self.value_label.setStyleSheet(
            f"color: {theme['text_main']}; background: transparent; border: none;"
        )
        self.sub_label.setStyleSheet(
            f"color: {theme['text_sec']}; background: transparent; border: none;"
        )
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {theme['bg_ter']};
                border-radius: 2px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {theme['accent']};
                border-radius: 2px;
            }}
        """)

    def set_value(self, text: str, sub_text: str = "", progress: int = -1):
        """设置卡片数据

        Args:
            text: 主数值文字
            sub_text: 副文字
            progress: 进度百分比 (0-100)，-1 表示不显示进度条
        """
        self.value_label.setText(text)
        self.sub_label.setText(sub_text)
        if progress >= 0:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.setVisible(False)


class HomeDashboard(QWidget):
    """首页仪表盘 — 4 张全局统计卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(138)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 卡片 1: 课程总览
        self.card_courses = StatCard("📚", "课程总览")
        layout.addWidget(self.card_courses, 1)

        # 卡片 2: 整体进度
        self.card_progress = StatCard("✅", "整体进度")
        layout.addWidget(self.card_progress, 1)

        # 卡片 3: 今日学习
        self.card_today = StatCard("⏱", "今日学习")
        layout.addWidget(self.card_today, 1)

        # 卡片 4: 连续学习
        self.card_streak = StatCard("🔥", "连续学习")
        layout.addWidget(self.card_streak, 1)

    def update_stats(self, total_courses: int, active_courses: int,
                      completed_videos: int, total_videos: int,
                      today_seconds: float, today_plan_seconds: float,
                      streak_days: int):
        """
        更新仪表盘数据。

        Args:
            total_courses: 课程总数
            active_courses: 进行中课程数
            completed_videos: 全部课程完成的视频数
            total_videos: 全部课程视频总数
            today_seconds: 今日累计学习时长（秒）
            today_plan_seconds: 今日累计计划时长（秒）
            streak_days: 连续学习天数
        """
        # 卡片 1: 课程总览
        if total_courses == 0:
            self.card_courses.set_value("0", "添加课程开始吧")
        else:
            self.card_courses.set_value(
                str(total_courses),
                f"{active_courses} 门进行中" if active_courses > 0 else "全部完成 🎉"
            )

        # 卡片 2: 整体进度
        if total_videos > 0:
            pct = int(completed_videos / total_videos * 100)
            self.card_progress.set_value(
                f"{pct}%",
                f"已完成 {completed_videos}/{total_videos} 个视频",
                progress=pct
            )
        else:
            self.card_progress.set_value("--", "暂无视频", progress=0)

        # 卡片 3: 今日学习
        today_str = self._format_duration(int(today_seconds))
        if today_plan_seconds > 0:
            plan_str = self._format_duration(int(today_plan_seconds))
            pct = min(100, int(today_seconds / today_plan_seconds * 100)) if today_plan_seconds > 0 else 0
            self.card_today.set_value(
                today_str,
                f"计划 {plan_str} · 完成 {pct}%",
                progress=pct
            )
        else:
            self.card_today.set_value(
                today_str if today_seconds > 0 else "--",
                "尚未设置学习计划"
            )

        # 卡片 4: 连续学习
        if streak_days > 0:
            self.card_streak.set_value(
                f"{streak_days} 天",
                "保持下去！💪" if streak_days >= 7 else "继续加油"
            )
        else:
            self.card_streak.set_value("0 天", "今天开始学习吧")

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """格式化秒数为可读时间字符串"""
        if seconds < 60:
            return f"{seconds}秒"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h{minutes:02d}m" if minutes > 0 else f"{hours}h"
        return f"{minutes}m"
