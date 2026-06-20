"""课程卡片组件 — 首页课程库的课程卡片，显示进度、时长、余额等信息"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QLineEdit
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from services.theme_service import theme_service
from utils.fonts import get_font


class CourseCard(QWidget):
    """课程卡片 — 展示单门课程的概览信息"""

    clicked = Signal()
    name_changed = Signal(str)  # 课程名称编辑完成

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._course_id = ""
        self._current_theme = None

        # ---- 主布局 ----
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 16, 20, 16)
        self.main_layout.setSpacing(14)

        # ---- 课程名称区域 ----
        self.course_info_layout = QHBoxLayout()
        self.course_info_layout.setSpacing(12)
        self.course_info_layout.setContentsMargins(0, 0, 0, 0)

        self.course_name_label = QLabel("课程名称")
        self.course_name_label.setFont(get_font("Bold", 15))
        self.course_name_label.setWordWrap(True)
        self.course_name_label.setMaximumWidth(300)
        self.course_info_layout.addWidget(self.course_name_label)

        # 内联编辑框（默认隐藏）
        self.name_edit = QLineEdit()
        self.name_edit.setVisible(False)
        self.name_edit.setFont(get_font("Bold", 15))
        self.name_edit.setMaximumWidth(300)
        self.name_edit.editingFinished.connect(self._on_name_edit_finished)
        self.course_info_layout.addWidget(self.name_edit)

        self.course_info_layout.addStretch()
        self.main_layout.addLayout(self.course_info_layout)

        # ---- 进度条区域 ----
        self.progress_layout = QVBoxLayout()
        self.progress_layout.setSpacing(8)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_label = QLabel("进度: 0%")
        self.progress_label.setFont(get_font("Regular", 11))
        self.progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_layout.addWidget(self.progress_bar)

        self.main_layout.addLayout(self.progress_layout)

        # ---- 时间信息区域 ----
        self.time_info_layout = QHBoxLayout()
        self.time_info_layout.setSpacing(25)
        self.time_info_layout.setContentsMargins(0, 0, 0, 0)

        # 课程总时长
        self.total_time_value = self._make_stat_group("课程总时长", "00:00 / 00:00")
        self.time_info_layout.addLayout(self.total_time_value["layout"])

        # 今日学习
        self.today_time_value = self._make_stat_group("今日学习", "00:00 / 00:00")
        self.time_info_layout.addLayout(self.today_time_value["layout"])

        # 预计剩余
        self.remaining_value = self._make_stat_group("预计剩余", "0天")
        self.time_info_layout.addLayout(self.remaining_value["layout"])

        # 学习余额
        self.balance_value = self._make_stat_group("学习余额", "+00:00")
        self.time_info_layout.addLayout(self.balance_value["layout"])

        self.time_info_layout.addStretch()
        self.main_layout.addLayout(self.time_info_layout)

        # ---- 主题 ----
        theme_service.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_service.get_theme())

        # ---- 进度动画 ----
        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(20)
        self.animation_timer.timeout.connect(self._animate_progress)
        self._target_progress = 0
        self._current_progress = 0

    @staticmethod
    def _make_stat_group(label_text: str, value_text: str) -> dict:
        """创建统计项布局（标签 + 值）"""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        label.setFont(get_font("Regular", 10))
        label.setObjectName("statLabel")
        layout.addWidget(label)

        value = QLabel(value_text)
        value.setFont(get_font("Bold", 13))
        value.setObjectName("statValue")
        layout.addWidget(value)

        return {"layout": layout, "label": label, "value": value}

    # ==================== 数据绑定 ====================

    def set_data(self, card_data):
        """
        一次性绑定所有展示数据（来自 Controller）。

        Args:
            card_data: CourseCardData 实例
        """
        self._course_id = card_data.course_id
        self.course_name_label.setText(card_data.course_name)
        self.name_edit.setText(card_data.course_name)

        # 进度
        self.set_progress(int(card_data.progress_percent))

        # 总时长
        watched_str = self._format_time(int(card_data.watched_sec))
        total_str = self._format_time(int(card_data.total_sec))
        self.total_time_value["value"].setText(f"{watched_str} / {total_str}")

        # 今日学习
        today_str = self._format_time(int(card_data.today_watched_sec))
        plan_str = self._format_time(int(card_data.today_plan_sec))
        self.today_time_value["value"].setText(f"{today_str} / {plan_str}")

        # 预计剩余
        self.remaining_value["value"].setText(f"{card_data.remaining_days}天")

        # 余额
        self.set_balance(card_data.balance_minutes)

    # ---- 保留逐个 setter 以兼容旧代码 ----

    def set_course_name(self, name: str):
        self.course_name_label.setText(name)
        self.name_edit.setText(name)

    def set_progress(self, progress: int):
        self._target_progress = max(0, min(100, progress))
        if not self.animation_timer.isActive():
            self.animation_timer.start()

    def set_total_time(self, watched_seconds: float, total_seconds: float):
        watched_str = self._format_time(int(watched_seconds))
        total_str = self._format_time(int(total_seconds))
        self.total_time_value["value"].setText(f"{watched_str} / {total_str}")

    def set_today_time(self, today_seconds: float, plan_seconds: float):
        today_str = self._format_time(int(today_seconds))
        plan_str = self._format_time(int(plan_seconds))
        self.today_time_value["value"].setText(f"{today_str} / {plan_str}")

    def set_remaining_days(self, days: int):
        self.remaining_value["value"].setText(f"{days}天")

    def set_balance(self, balance_minutes: float):
        balance_str = self._format_time(int(abs(balance_minutes) * 60))
        if balance_minutes >= 0:
            self.balance_value["value"].setText(f"+{balance_str}")
        else:
            self.balance_value["value"].setText(f"-{balance_str}")

        # 余额颜色在 _apply_theme 中根据当前主题处理
        self._update_balance_color()

    # ==================== 进度动画 ====================

    def _animate_progress(self):
        if self._current_progress < self._target_progress:
            self._current_progress += 1
            if self._current_progress > self._target_progress:
                self._current_progress = self._target_progress
        elif self._current_progress > self._target_progress:
            self._current_progress -= 1
            if self._current_progress < self._target_progress:
                self._current_progress = self._target_progress
        else:
            self.animation_timer.stop()

        self.progress_bar.setValue(self._current_progress)
        self.progress_label.setText(f"进度: {self._current_progress}%")

    # ==================== 主题 ====================

    def _apply_theme(self, theme):
        self._current_theme = theme
        bg_color = theme["bg_sec"]
        text_color = theme["text_main"]
        text_sec = theme["text_sec"]
        border_color = theme["border"]
        accent = theme["accent"]

        self.setStyleSheet(f"""
            CourseCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)

        self.course_name_label.setStyleSheet(f"color: {text_color}; font-weight: bold; background: transparent;")
        self.progress_label.setStyleSheet(f"color: {text_sec}; background: transparent;")

        # 进度条
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {border_color};
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {accent};
                border-radius: 4px;
            }}
        """)

        # 统计标签
        for group in [self.total_time_value, self.today_time_value,
                       self.remaining_value, self.balance_value]:
            group["label"].setStyleSheet(f"color: {text_sec}; background: transparent;")
            group["value"].setStyleSheet(f"color: {text_color}; font-weight: bold; background: transparent;")

        self._update_balance_color()

    def _update_balance_color(self):
        """根据余额正负设置颜色"""
        if not self._current_theme:
            return
        text = self.balance_value["value"].text()
        if text.startswith("+"):
            self.balance_value["value"].setStyleSheet(
                f"color: #4CAF50; font-weight: bold; background: transparent;"
            )
        elif text.startswith("-"):
            self.balance_value["value"].setStyleSheet(
                f"color: #F44336; font-weight: bold; background: transparent;"
            )

    # ==================== 交互 ====================

    def mouseDoubleClickEvent(self, event):
        """双击进入名称编辑模式"""
        self.course_name_label.setVisible(False)
        self.name_edit.setVisible(True)
        self.name_edit.setFocus()
        self.name_edit.selectAll()
        super().mouseDoubleClickEvent(event)

    def _on_name_edit_finished(self):
        """名称编辑完成"""
        new_name = self.name_edit.text().strip()
        self.course_name_label.setVisible(True)
        self.name_edit.setVisible(False)
        if new_name and new_name != self.course_name_label.text():
            self.course_name_label.setText(new_name)
            self.name_changed.emit(new_name)

    def enterEvent(self, event):
        if self._current_theme:
            is_light = self._current_theme["name"] == "light"
            accent = self._current_theme["accent"]
            hover_bg = "#F0F7FF" if is_light else "#1E3A5F"
            self.setStyleSheet(f"""
                CourseCard {{
                    background-color: {hover_bg};
                    border: 1px solid {accent};
                    border-radius: 12px;
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._current_theme:
            self._apply_theme(self._current_theme)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    # ==================== 工具方法 ====================

    @staticmethod
    def _format_time(seconds: int) -> str:
        """格式化秒数为 HH:MM"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
