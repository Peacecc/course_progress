"""目标倒计时组件 — 首页仪表盘左侧，显示最近完成日期倒计时"""

from datetime import date, datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from services.theme_service import theme_service
from utils.fonts import get_font


class GoalCountdownWidget(QWidget):
    """显示"距离目标完成还有 X 天"的倒计时卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)

        # 标题
        self.title_label = QLabel("📅 学习目标")
        self.title_label.setFont(get_font("Regular", 11))

        # 倒计时数字
        self.countdown_label = QLabel("--")
        self.countdown_label.setFont(get_font("Bold", 36))
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 描述
        self.desc_label = QLabel("添加课程并设置计划开始")
        self.desc_label.setFont(get_font("Regular", 10))
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.countdown_label)
        layout.addWidget(self.desc_label)

        theme_service.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_service.get_theme())

    def _apply_theme(self, theme):
        is_light = theme["name"] == "light"
        border_color = theme["border"]

        self.setStyleSheet(f"""
            GoalCountdownWidget {{
                background-color: {theme['bg_sec']};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        self.title_label.setStyleSheet(f"color: {theme['text_sec']}; background: transparent; border: none;")
        self.countdown_label.setStyleSheet(
            f"color: {theme['accent']}; background: transparent; border: none;"
        )
        self.desc_label.setStyleSheet(f"color: {theme['text_sec']}; background: transparent; border: none;")

    def set_nearest_deadline(self, days: int, course_name: str = ""):
        """
        设置最近的截止日期。

        Args:
            days: 距离完成的天数（-1 表示全部完成，0 表示无计划）
            course_name: 对应的课程名称
        """
        if days < 0:
            self.countdown_label.setText("🎉")
            self.desc_label.setText("全部课程已完成！")
        elif days == 0:
            self.countdown_label.setText("--")
            self.desc_label.setText("设置学习计划开始追踪")
        else:
            self.countdown_label.setText(str(days))
            suffix = f"\n{course_name}" if course_name else ""
            self.desc_label.setText(f"天 到达目标{suffix}")

    def set_multi_course_summary(self, total_courses: int, active_courses: int):
        """多课程概览模式"""
        if total_courses == 0:
            self.countdown_label.setText("0")
            self.desc_label.setText("门课程，点击 + 添加")
        else:
            self.countdown_label.setText(str(total_courses))
            self.desc_label.setText(f"门课程 | {active_courses} 门进行中")
