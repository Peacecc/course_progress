"""首页热力图组件 — 聚合所有课程的学习数据，显示年度学习热力图"""

from datetime import date, timedelta

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont

from services.theme_service import theme_service


class HomeHeatMapWidget(QWidget):
    """聚合所有课程每日学习时长的年度热力图（GitHub 贡献图风格）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(130)

        self._all_daily_stats = {}  # {date_str: total_seconds}
        self._target_hours = 1.0    # 基准目标（用于颜色分级）

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(0)

        # 标题在内部绘制，不额外占空间
        self.setMinimumSize(400, 130)

        theme_service.theme_changed.connect(lambda t: self.update())
        self._apply_base_style()

    def _apply_base_style(self):
        theme = theme_service.get_theme()
        self.setStyleSheet(f"""
            HomeHeatMapWidget {{
                background-color: {theme['bg_sec']};
                border: 1px solid {theme['border']};
                border-radius: 12px;
            }}
        """)

    def set_data(self, all_daily_stats: dict, target_hours: float = 1.0):
        """
        设置热力图数据。

        Args:
            all_daily_stats: 聚合后的每日统计 {date_str: total_seconds}
            target_hours: 基准目标（小时/天），用于颜色分级
        """
        self._all_daily_stats = all_daily_stats
        self._target_hours = max(target_hours, 0.1)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        theme = theme_service.get_theme()
        w = self.width()
        h = self.height()

        # ---- 标题 ----
        title_font = QFont("Microsoft YaHei", 11)
        painter.setFont(title_font)
        painter.setPen(QColor(theme["text_sec"]))
        painter.drawText(16, 22, "📊 学习热力图（近 6 个月）")

        # ---- 参数 ----
        cell_size = 12
        cell_gap = 3
        step = cell_size + cell_gap
        cols = 27  # 最多 27 周 ≈ 6 个月
        rows = 7   # 周一~周日

        start_x = 24
        start_y = 38

        # ---- 颜色阶梯 ----
        base_color = QColor(theme["bg_ter"])
        c1 = QColor(theme["accent"]); c1.setAlpha(50)
        c2 = QColor(theme["accent"]); c2.setAlpha(100)
        c3 = QColor(theme["accent"]); c3.setAlpha(170)
        c4 = QColor(theme["accent"])

        # ---- 生成日期网格 ----
        today = date.today()
        # 从最后一个周日开始，往前推 cols 周
        end_sunday = today - timedelta(days=today.weekday() + 1)  # 上周日
        if today.weekday() == 6:
            end_sunday = today
        start_date = end_sunday - timedelta(weeks=cols - 1)

        # 月份标签位置
        month_positions = {}  # col -> month_label
        iter_date = start_date
        for col in range(cols):
            if iter_date.day <= 7 or col == 0:
                month_positions[col] = f"{iter_date.month}月"
            iter_date += timedelta(weeks=1)

        # 绘制月份标签
        month_font = QFont("Microsoft YaHei", 8)
        painter.setFont(month_font)
        painter.setPen(QColor(theme["text_sec"]))
        for col, label in month_positions.items():
            x = start_x + col * step
            painter.drawText(x, start_y - 6, label)

        # 绘制星期标签（左侧）
        day_names = ["一", "二", "三", "四", "五", "六", "日"]
        day_font = QFont("Microsoft YaHei", 8)
        painter.setFont(day_font)
        for row in range(rows):
            y = start_y + row * step
            painter.drawText(4, y + cell_size - 2, day_names[row])

        # 绘制格子
        iter_date = start_date
        for col in range(cols):
            # 获取这周的起始周一的日期
            week_start = start_date + timedelta(weeks=col)
            for row in range(rows):
                d = week_start + timedelta(days=row)
                if d > today:
                    continue

                d_str = d.strftime("%Y-%m-%d")
                secs = self._all_daily_stats.get(d_str, 0)
                hours = secs / 3600.0

                x = start_x + col * step
                y = start_y + row * step

                # 颜色映射
                if hours <= 0:
                    color = base_color
                else:
                    ratio = hours / self._target_hours
                    if ratio >= 2.0:
                        color = c4
                    elif ratio >= 1.0:
                        color = c3
                    elif ratio >= 0.5:
                        color = c2
                    else:
                        color = c1

                painter.setBrush(QBrush(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(x, y, cell_size, cell_size, 2, 2)

        painter.end()
