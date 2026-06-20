"""课程卡片组件 — 首页课程库的课程卡片，显示进度、时长、余额等信息"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QProgressBar, QLineEdit, QPushButton, QStackedWidget,
)
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PySide6.QtGui import QColor

from services.theme_service import theme_service
from utils.fonts import get_font


class CourseCard(QWidget):
    """课程卡片 — 展示单门课程的概览信息，适配多列网格布局"""

    clicked = Signal()
    name_changed = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(200)
        self.setMinimumWidth(300)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._course_id = ""
        self._current_theme = None
        self._hover_progress = 0.0

        # ---- 主布局 ----
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ==================== 顶部强调色条 ====================
        self.accent_bar = QWidget()
        self.accent_bar.setFixedHeight(3)
        self.main_layout.addWidget(self.accent_bar)

        # ==================== 卡片内容区 ====================
        content = QVBoxLayout()
        content.setContentsMargins(18, 12, 14, 14)
        content.setSpacing(10)

        # ---- Row 0: 名称行 ----
        name_row = QHBoxLayout()
        name_row.setContentsMargins(0, 0, 0, 0)
        name_row.setSpacing(8)

        self.name_stack = QStackedWidget()

        self.course_name_label = QLabel("课程名称")
        self.course_name_label.setFont(get_font("Bold", 14))
        self.course_name_label.setWordWrap(True)
        self.course_name_label.setMaximumWidth(240)
        self.name_stack.addWidget(self.course_name_label)  # index 0

        self.name_edit = QLineEdit()
        self.name_edit.setFont(get_font("Bold", 14))
        self.name_edit.setMaximumWidth(240)
        self.name_edit.editingFinished.connect(self._on_name_edit_finished)
        self.name_stack.addWidget(self.name_edit)  # index 1

        name_row.addWidget(self.name_stack)
        name_row.addStretch()

        self.delete_btn = QPushButton("\U0001F5D1")
        self.delete_btn.setFixedSize(26, 26)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setToolTip("删除课程")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        name_row.addWidget(self.delete_btn)

        content.addLayout(name_row)

        # ---- Row 1: 进度条 + 百分比（同行） ----
        progress_row = QHBoxLayout()
        progress_row.setContentsMargins(0, 0, 0, 0)
        progress_row.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        progress_row.addWidget(self.progress_bar, 1)  # stretch=1：占满剩余空间

        self.progress_pct_label = QLabel("0%")
        self.progress_pct_label.setFont(get_font("Bold", 16))
        self.progress_pct_label.setFixedWidth(48)
        self.progress_pct_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        progress_row.addWidget(self.progress_pct_label)

        content.addLayout(progress_row)

        # ---- Row 2-3: 统计网格 (2×2) ----
        stats_grid = QGridLayout()
        stats_grid.setContentsMargins(0, 2, 0, 0)
        stats_grid.setHorizontalSpacing(20)
        stats_grid.setVerticalSpacing(6)

        self.total_time_value = self._make_stat_group("⏱ 课程总时长", "00:00 / 00:00")
        stats_grid.addLayout(self.total_time_value["layout"], 0, 0)

        self.today_time_value = self._make_stat_group("\U0001F4D6 今日学习", "00:00 / 00:00")
        stats_grid.addLayout(self.today_time_value["layout"], 0, 1)

        self.remaining_value = self._make_stat_group("\U0001F4C5 预计剩余", "0天")
        stats_grid.addLayout(self.remaining_value["layout"], 1, 0)

        self.balance_value = self._make_stat_group("⚖ 学习余额", "+00:00")
        stats_grid.addLayout(self.balance_value["layout"], 1, 1)

        stats_grid.setColumnStretch(0, 1)
        stats_grid.setColumnStretch(1, 1)
        content.addLayout(stats_grid)

        self.main_layout.addLayout(content)

        # ---- 主题 ----
        theme_service.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_service.get_theme())

    def sizeHint(self):
        return QSize(360, 200)

    # ==================== 自定义属性 ====================

    @Property(float)
    def hoverProgress(self):
        return self._hover_progress

    @hoverProgress.setter
    def hoverProgress(self, value):
        self._hover_progress = value
        self._apply_hover_state()

    # ==================== 数据绑定 ====================

    def set_data(self, card_data):
        self._course_id = card_data.course_id
        self.course_name_label.setText(card_data.course_name)
        self.name_edit.setText(card_data.course_name)
        self.set_progress(int(card_data.progress_percent))

        watched_str = self._format_time(int(card_data.watched_sec))
        total_str = self._format_time(int(card_data.total_sec))
        self.total_time_value["value"].setText(f"{watched_str} / {total_str}")

        today_str = self._format_time(int(card_data.today_watched_sec))
        plan_str = self._format_time(int(card_data.today_plan_sec))
        self.today_time_value["value"].setText(f"{today_str} / {plan_str}")

        self.remaining_value["value"].setText(f"{card_data.remaining_days}天")
        self.set_balance(card_data.balance_minutes)

    def set_course_name(self, name: str):
        self.course_name_label.setText(name)
        self.name_edit.setText(name)

    def set_progress(self, progress: int):
        target = max(0, min(100, progress))
        self._anim_progress = QPropertyAnimation(self.progress_bar, b"value")
        self._anim_progress.setDuration(400)
        self._anim_progress.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_progress.setStartValue(self.progress_bar.value())
        self._anim_progress.setEndValue(target)
        self._anim_progress.valueChanged.connect(
            lambda v: self.progress_pct_label.setText(f"{int(v)}%")
        )
        self._anim_progress.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

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
        self._update_balance_color()

    # ==================== 悬停动画 ====================

    def _apply_hover_state(self):
        """悬停状态 — 三层 accent 驱动的视觉变化，无阴影"""
        if not self._current_theme:
            return
        t = self._hover_progress
        theme = self._current_theme
        accent = theme["accent"]
        is_light = theme["name"] == "light"

        # 1. 背景：混入 10% accent 色，形成主题色淡色调
        mix_ratio = 0.08 if is_light else 0.12
        tinted_bg = self._interpolate_color(theme["bg_sec"], accent, mix_ratio)
        bg = self._interpolate_color(theme["bg_sec"], tinted_bg, t)

        # 2. 边框：从默认色过渡到 accent 色
        border = self._interpolate_color(theme["border"], accent, t)

        # 3. 顶部强调色条：3px → 12px（像"电源条"激活）
        bar_h = int(3 + t * 9)
        self.accent_bar.setFixedHeight(bar_h)
        # 强调色条本身也微微向更亮的 accent 过渡
        bar_color = self._interpolate_color(accent, self._lighten_color(accent, 0.3), t)
        self.accent_bar.setStyleSheet(
            f"background-color: {bar_color}; border: none; border-radius: 0px;"
        )

        # 4. 百分比标签：从 accent 过渡到更亮的变体
        pct_color = self._interpolate_color(accent, self._lighten_color(accent, 0.35), t)
        self.progress_pct_label.setStyleSheet(
            f"color: {pct_color}; background: transparent; font-weight: bold;"
        )

        self.setStyleSheet(self._build_card_stylesheet(bg, border, theme))

    @staticmethod
    def _lighten_color(hex_color: str, factor: float) -> str:
        """将颜色向白色方向提亮 factor（0~1）"""
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _build_card_stylesheet(self, bg: str, border: str, theme: dict) -> str:
        return f"""
            CourseCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
        """

    @staticmethod
    def _interpolate_color(hex_from: str, hex_to: str, t: float) -> str:
        t = max(0.0, min(1.0, t))
        r1, g1, b1 = int(hex_from[1:3], 16), int(hex_from[3:5], 16), int(hex_from[5:7], 16)
        r2, g2, b2 = int(hex_to[1:3], 16), int(hex_to[3:5], 16), int(hex_to[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def enterEvent(self, event):
        self._anim_hover = QPropertyAnimation(self, b"hoverProgress")
        self._anim_hover.setDuration(250)
        self._anim_hover.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_hover.setStartValue(self._hover_progress)
        self._anim_hover.setEndValue(1.0)
        self._anim_hover.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim_hover = QPropertyAnimation(self, b"hoverProgress")
        self._anim_hover.setDuration(300)
        self._anim_hover.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_hover.setStartValue(self._hover_progress)
        self._anim_hover.setEndValue(0.0)
        self._anim_hover.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        super().leaveEvent(event)

    # ==================== 交互 ====================

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            if child is self.delete_btn:
                super().mousePressEvent(event)
                return

            if self._current_theme:
                theme = self._current_theme
                self.setStyleSheet(self._build_card_stylesheet(
                    theme["bg_ter"], theme["accent"], theme
                ))
                QTimer.singleShot(100, self._apply_hover_state)

            self.clicked.emit()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        child = self.childAt(event.position().toPoint())
        if child is self.delete_btn:
            super().mouseDoubleClickEvent(event)
            return

        self.name_stack.setCurrentIndex(1)
        self.name_edit.setFocus()
        self.name_edit.selectAll()
        super().mouseDoubleClickEvent(event)

    def _on_name_edit_finished(self):
        new_name = self.name_edit.text().strip()
        self.name_stack.setCurrentIndex(0)
        if new_name and new_name != self.course_name_label.text():
            self.course_name_label.setText(new_name)
            self.name_changed.emit(new_name)

    def _on_delete_clicked(self):
        self.delete_requested.emit(self._course_id)

    # ==================== 主题 ====================

    def _apply_theme(self, theme):
        self._current_theme = theme
        text_color = theme["text_main"]
        text_sec = theme["text_sec"]
        border_color = theme["border"]
        accent = theme["accent"]
        danger = theme["danger"]
        bg_ter = theme["bg_ter"]

        # 强调色条（重置为默认高度 3px）
        self.accent_bar.setFixedHeight(3)
        self.accent_bar.setStyleSheet(
            f"background-color: {accent}; border: none; border-radius: 0px;"
        )

        # 卡片背景/边框
        self.setStyleSheet(self._build_card_stylesheet(theme["bg_sec"], border_color, theme))

        # 课程名称
        self.course_name_label.setStyleSheet(
            f"color: {text_color}; font-weight: bold; background: transparent;"
        )

        # 百分比标签（accent 色，hover 时会动态提亮）
        self.progress_pct_label.setStyleSheet(
            f"color: {accent}; background: transparent; font-weight: bold;"
        )

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

        # 垃圾桶按钮
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 13px;
                color: {text_sec};
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: {danger};
                background: {bg_ter};
            }}
        """)

        # 统计标签
        for group in [self.total_time_value, self.today_time_value,
                       self.remaining_value, self.balance_value]:
            group["label"].setStyleSheet(f"color: {text_sec}; background: transparent;")
            group["value"].setStyleSheet(f"color: {text_color}; font-weight: bold; background: transparent;")

        self._update_balance_color()

    def _update_balance_color(self):
        if not self._current_theme:
            return
        text = self.balance_value["value"].text()
        if text.startswith("+"):
            self.balance_value["value"].setStyleSheet(
                "color: #4CAF50; font-weight: bold; background: transparent;"
            )
        elif text.startswith("-"):
            self.balance_value["value"].setStyleSheet(
                "color: #F44336; font-weight: bold; background: transparent;"
            )

    # ==================== 工具方法 ====================

    @staticmethod
    def _make_stat_group(label_text: str, value_text: str) -> dict:
        layout = QVBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        label.setFont(get_font("Regular", 9))
        label.setObjectName("statLabel")
        layout.addWidget(label)

        value = QLabel(value_text)
        value.setFont(get_font("Bold", 12))
        value.setObjectName("statValue")
        layout.addWidget(value)

        return {"layout": layout, "label": label, "value": value}

    @staticmethod
    def _format_time(seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
