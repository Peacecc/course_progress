"""课程时间线组件 — 可视化展示从开始到预计完成的学习旅程"""

from datetime import date, datetime, timedelta

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont, QFontMetrics, QPainterPath

from services.theme_service import theme_service
from utils.fonts import get_font


class CourseTimeline(QWidget):
    """学习时间线 — 开始日期 → 今天 → 预计完成（纯可视化）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CourseTimeline")
        self.setMinimumHeight(140)

        self._start_date = None
        self._today = date.today()
        self._estimated_finish = None
        self._progress_pct = 0.0
        self._balance_hours = 0.0
        self._total_days = 0
        self._elapsed_days = 0
        self._is_completed = False
        self._has_plan = False

        # ---- 布局 ----
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # 标题行
        header = QHBoxLayout()
        self.title_label = QLabel("🚩 学习时间线")
        self.title_label.setFont(get_font("Bold", 13))
        header.addWidget(self.title_label)
        header.addStretch()

        # 预计完成标签
        self.finish_label = QLabel("")
        self.finish_label.setFont(get_font("Regular", 11))
        header.addWidget(self.finish_label)
        main_layout.addLayout(header)

        # 时间线画布区域
        self.canvas = _TimelineCanvas(self)
        self.canvas.setMinimumHeight(90)
        main_layout.addWidget(self.canvas)

        theme_service.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_service.get_theme())

    def _apply_theme(self, theme):
        self.setStyleSheet(f"""
            #CourseTimeline {{
                background-color: {theme['bg_sec']};
                border: 1px solid {theme['border']};
                border-radius: 12px;
            }}
        """)
        self.title_label.setStyleSheet(
            f"color: {theme['text_main']}; background: transparent; border: none;"
        )
        self.finish_label.setStyleSheet(
            f"color: {theme['text_sec']}; background: transparent; border: none;"
        )
        self.canvas._theme = theme
        self.canvas.update()

    def set_data(self, start_date_iso: str, estimated_finish: str,
                  balance_hours: float, progress_pct: float,
                  total_videos: int, completed_videos: int):
        """
        更新时间线数据。

        Args:
            start_date_iso: 开始日期 ISO 字符串
            estimated_finish: 预计完成日期字符串
            balance_hours: 学习余额（小时）
            progress_pct: 进度百分比
            total_videos: 总视频数
            completed_videos: 已完成视频数
        """
        self._balance_hours = balance_hours
        self._progress_pct = progress_pct
        self._has_plan = bool(start_date_iso)
        self._is_completed = (estimated_finish == "已完成")

        # 解析日期
        today = date.today()
        self._today = today

        if start_date_iso:
            try:
                self._start_date = datetime.fromisoformat(start_date_iso).date()
            except (ValueError, TypeError):
                self._start_date = None
        else:
            self._start_date = None

        if estimated_finish and estimated_finish not in ("--", "已完成"):
            try:
                self._estimated_finish = datetime.fromisoformat(estimated_finish).date()
            except (ValueError, TypeError):
                self._estimated_finish = None
        elif estimated_finish == "已完成":
            self._estimated_finish = today
        else:
            self._estimated_finish = None

        # 计算时间线参数
        if self._start_date and self._estimated_finish:
            self._total_days = max(1, (self._estimated_finish - self._start_date).days)
            self._elapsed_days = max(0, (today - self._start_date).days)
        else:
            self._total_days = 0
            self._elapsed_days = 0

        # 更新 UI
        if self._estimated_finish and self._estimated_finish != today:
            self.finish_label.setText(f"🏁 {self._estimated_finish.strftime('%Y-%m-%d')}")
        elif self._is_completed:
            self.finish_label.setText("🎉 课程已完成")
        else:
            self.finish_label.setText("")

        # 画布
        self.canvas._start_date = self._start_date
        self.canvas._today = today
        self.canvas._estimated_finish = self._estimated_finish
        self.canvas._progress_pct = self._progress_pct
        self.canvas._elapsed_days = self._elapsed_days
        self.canvas._total_days = self._total_days
        self.canvas._has_plan = self._has_plan
        self.canvas._is_completed = self._is_completed
        self.canvas.update()

class _TimelineCanvas(QWidget):
    """时间线画布 — 纯绘制"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._start_date = None
        self._today = date.today()
        self._estimated_finish = None
        self._progress_pct = 0.0
        self._elapsed_days = 0
        self._total_days = 0
        self._has_plan = False
        self._is_completed = False
        self._theme = theme_service.get_theme()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        theme = self._theme
        w = self.width()
        h = self.height()

        # 原点 — bar 放在画布偏上位置，给下方文字留空间
        margin_x = 10
        bar_y = int(h * 0.38)
        bar_h = 14
        bar_w = w - 2 * margin_x

        # 背景轨道
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(theme["bg_ter"])))
        painter.drawRoundedRect(margin_x, bar_y - bar_h // 2, bar_w, bar_h, bar_h // 2, bar_h // 2)

        if not self._has_plan:
            # 无计划状态：灰色轨道 + 居中提示
            painter.setPen(QColor(theme["text_sec"]))
            font = get_font("Regular", 11)
            painter.setFont(font)
            fm = painter.fontMetrics()
            hint_text = "设置开始日期和周计划后，这里将显示学习进度时间线"
            hint_w = fm.horizontalAdvance(hint_text)
            painter.drawText(int(margin_x + (bar_w - hint_w) / 2), bar_y + fm.ascent() // 2, hint_text)
            return

        if self._is_completed:
            # 全部完成：满条
            painter.setBrush(QBrush(QColor("#4CAF50")))
            painter.drawRoundedRect(margin_x, bar_y - bar_h // 2, bar_w, bar_h, bar_h // 2, bar_h // 2)
            painter.setPen(QColor(theme["text_main"]))
            font = get_font("Bold", 11)
            painter.setFont(font)
            fm = painter.fontMetrics()
            done_text = "🎉 课程已完成"
            done_w = fm.horizontalAdvance(done_text)
            painter.drawText(int(margin_x + (bar_w - done_w) / 2), bar_y + fm.ascent() // 2, done_text)
            return

        # 已完成部分
        filled_w = int(bar_w * min(1.0, self._progress_pct / 100.0))
        if filled_w > 0:
            painter.setBrush(QBrush(QColor(theme["accent"])))
            painter.drawRoundedRect(margin_x, bar_y - bar_h // 2, filled_w, bar_h, bar_h // 2, bar_h // 2)

        # 今天标记
        if self._total_days > 0 and self._start_date:
            today_fraction = min(1.0, self._elapsed_days / self._total_days)
            today_x = margin_x + int(bar_w * today_fraction)

            # 竖线
            painter.setPen(QPen(QColor(theme["text_main"]), 2))
            painter.drawLine(today_x, bar_y - 20, today_x, bar_y + 20)

            # 圆点
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(theme["text_main"])))
            painter.drawEllipse(today_x - 4, bar_y - 4, 8, 8)

            # "今天" 标签
            painter.setPen(QColor(theme["text_main"]))
            font = get_font("Bold", 9)
            painter.setFont(font)
            fm = painter.fontMetrics()
            today_text_w = fm.horizontalAdvance("今天")
            painter.drawText(today_x - today_text_w // 2, bar_y + 26 + fm.ascent(), "今天")

            # 进度百分比（在已填充区域内部）
            if filled_w > 44:
                painter.setPen(QColor("white"))
                font = get_font("Bold", 9)
                painter.setFont(font)
                painter.drawText(margin_x + 8, bar_y + 5, f"{self._progress_pct:.0f}%")

        # 日期标签 — 画在 bar 上方
        date_font = get_font("Regular", 9)
        date_metrics = QFontMetrics(date_font)
        date_y = bar_y - bar_h // 2 - 4

        if self._start_date:
            painter.setPen(QColor(theme["text_sec"]))
            painter.setFont(date_font)
            painter.drawText(margin_x, date_y, self._start_date.strftime("%Y-%m-%d"))

        if self._estimated_finish:
            painter.setPen(QColor(theme["text_sec"]))
            painter.setFont(date_font)
            finish_text = self._estimated_finish.strftime("%Y-%m-%d")
            finish_w = date_metrics.horizontalAdvance(finish_text)
            painter.drawText(margin_x + bar_w - finish_w, date_y, finish_text)

        # 底部天数统计 — 画在 bar 下方
        if self._total_days > 0:
            painter.setPen(QColor(theme["text_sec"]))
            days_font = get_font("Regular", 10)
            painter.setFont(days_font)
            days_fm = painter.fontMetrics()
            days_text = f"已过 {self._elapsed_days} / {self._total_days} 天"
            days_w = days_fm.horizontalAdvance(days_text)
            days_y = bar_y + bar_h // 2 + days_fm.ascent() + 8
            painter.drawText(margin_x + bar_w // 2 - days_w // 2, days_y, days_text)
