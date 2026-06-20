"""课程看板视图 — 进度总览 + 学习时间线 + 周计划"""

from datetime import date, datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QSlider, QSizePolicy, QStyleOptionSlider,
    QStyle, QScrollArea, QProgressBar, QStackedWidget, QDialog,
)
from PySide6.QtCore import Qt, QDate, Signal, QPoint
from PySide6.QtGui import QFont

from services.theme_service import theme_service as theme_manager
from utils.fonts import get_font
from views.widgets.ela_date_picker import ElaDatePicker
from views.widgets.course_timeline import CourseTimeline


# ==================== 可点击滑块 ====================

class ClickableSlider(QSlider):
    """支持点击跳转的滑块"""

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setValue(self._pixel_pos_to_value(event.position().toPoint()))
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.setValue(self._pixel_pos_to_value(event.position().toPoint()))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def _pixel_pos_to_value(self, pos: QPoint) -> int:
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
        sr = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderHandle, self)
        if self.orientation() == Qt.Orientation.Vertical:
            slider_len = sr.height()
            slider_min = gr.y()
            slider_max = gr.y() + gr.height() - slider_len + 1
            prop = 1.0 - (pos.y() - slider_min) / (slider_max - slider_min)
        else:
            slider_len = sr.width()
            slider_min = gr.x()
            slider_max = gr.x() + gr.width() - slider_len + 1
            prop = (pos.x() - slider_min) / (slider_max - slider_min)
        return int(self.minimum() + prop * (self.maximum() - self.minimum()))


# ==================== 每日滑块（纵向旧版，保留兼容） ====================

class DailySlider(QWidget):
    """单日学习时长滑块（垂直）"""
    value_changed = Signal(float)

    def __init__(self, day_name: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.val_label = QLabel("0h")
        self.val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.val_label, 0, Qt.AlignmentFlag.AlignHCenter)

        self.slider = ClickableSlider(Qt.Orientation.Vertical)
        self.slider.setRange(0, 72)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(6)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setFixedHeight(110)
        self.slider.valueChanged.connect(self._on_slider_change)
        layout.addWidget(self.slider, 0, Qt.AlignmentFlag.AlignHCenter)

        self.day_label = QLabel(day_name)
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.day_label, 0, Qt.AlignmentFlag.AlignHCenter)

        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_manager.get_theme())

    def _on_slider_change(self, val: int):
        minutes = val * 10
        h = minutes // 60
        m = minutes % 60
        self.val_label.setText(f"{h}h" if m == 0 else f"{h}h{m}")
        self.value_changed.emit(minutes / 60.0)

    def set_value(self, hours: float):
        self.slider.blockSignals(True)
        self.slider.setValue(min(int(hours * 6), 72))
        self.slider.blockSignals(False)

    def get_value(self) -> float:
        return self.slider.value() / 6.0

    def set_locked(self, locked: bool):
        self.slider.setEnabled(not locked)

    def _apply_theme(self, theme):
        self.val_label.setStyleSheet(
            f"color: {theme['accent']}; font-weight: bold; font-size: 11px; background: transparent;")
        self.day_label.setStyleSheet(
            f"color: {theme['text_main']}; font-size: 12px; background: transparent;")
        self.slider.setStyleSheet(f"""
            QSlider::groove:vertical {{
                background: {theme['bg_ter']}; width: 14px; border-radius: 7px;
            }}
            QSlider::sub-page:vertical {{
                background: {theme['accent']};
                border-bottom-left-radius: 7px; border-bottom-right-radius: 7px;
                border-top-left-radius: 0px; border-top-right-radius: 0px;
            }}
            QSlider::handle:vertical {{
                background: {theme['accent']}; height: 14px; width: 14px;
                border-radius: 7px; margin: 0px; border: none;
            }}
            QSlider::sub-page:vertical:disabled {{ background: {theme['text_sec']}; }}
            QSlider::handle:vertical:disabled {{ background: {theme['text_sec']}; }}
        """)


# ==================== 横向每日滑块（新版） ====================

class DaySlider(QWidget):
    """单日学习时长滑块（横向，紧凑 — 用于周计划每日微调）"""
    value_changed = Signal(float)

    def __init__(self, day_name: str, parent=None):
        super().__init__(parent)
        self.setFixedWidth(72)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.day_label = QLabel(day_name)
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_label.setFont(get_font("Bold", 11))
        layout.addWidget(self.day_label, 0, Qt.AlignmentFlag.AlignHCenter)

        self.slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 72)       # 0–12h, 10min/step
        self.slider.setSingleStep(3)       # 0.5h
        self.slider.setPageStep(6)         # 1h
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setFixedHeight(20)
        self.slider.valueChanged.connect(self._on_slider_change)
        layout.addWidget(self.slider, 0, Qt.AlignmentFlag.AlignHCenter)

        self.val_label = QLabel("0h")
        self.val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.val_label.setFont(get_font("Bold", 10))
        layout.addWidget(self.val_label, 0, Qt.AlignmentFlag.AlignHCenter)

        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_manager.get_theme())

    def _on_slider_change(self, val: int):
        hours = val / 6.0
        self.val_label.setText(f"{int(hours)}h" if hours == int(hours) else f"{hours:.1f}h")
        self.value_changed.emit(hours)

    def set_value(self, hours: float):
        self.slider.blockSignals(True)
        self.slider.setValue(min(int(hours * 6), 72))
        self.slider.blockSignals(False)
        h = self.slider.value() / 6.0
        self.val_label.setText(f"{int(h)}h" if h == int(h) else f"{h:.1f}h")

    def get_value(self) -> float:
        return self.slider.value() / 6.0

    def set_enabled(self, enabled: bool):
        self.slider.setEnabled(enabled)

    def _apply_theme(self, theme):
        self.day_label.setStyleSheet(
            f"color: {theme['text_main']}; background: transparent; border: none;")
        self.val_label.setStyleSheet(
            f"color: {theme['accent']}; background: transparent; border: none;")
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {theme['bg_ter']}; height: 6px; border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme['accent']};
                border-top-left-radius: 3px; border-bottom-left-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {theme['accent']}; width: 14px; height: 14px;
                border-radius: 7px; margin: -4px 0px; border: none;
            }}
            QSlider::sub-page:horizontal:disabled {{ background: {theme['text_sec']}; }}
            QSlider::handle:horizontal:disabled {{ background: {theme['text_sec']}; }}
        """)


# ==================== 统计卡片 ====================

class _StatCard(QFrame):
    """单张统计卡片"""

    def __init__(self, icon: str, title: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(115)
        self.setObjectName("StatCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(6)
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 14))
        header.addWidget(icon_label)
        title_label = QLabel(title)
        title_label.setFont(get_font("Regular", 11))
        title_label.setObjectName("cardTitle")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        self.value_label = QLabel("--")
        self.value_label.setFont(get_font("Bold", 20))
        self.value_label.setObjectName("cardValue")
        layout.addWidget(self.value_label)

        self.sub_label = QLabel("")
        self.sub_label.setFont(get_font("Regular", 10))
        self.sub_label.setObjectName("cardSub")
        layout.addWidget(self.sub_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_manager.get_theme())

    def _apply_theme(self, theme):
        self.setStyleSheet(f"""
            _StatCard {{
                background-color: {theme['bg_sec']};
                border: 1px solid {theme['border']};
                border-radius: 12px;
            }}
            QLabel#cardTitle {{ color: {theme['text_sec']}; background: transparent; border: none; }}
            QLabel#cardValue {{ color: {theme['text_main']}; background: transparent; border: none; }}
            QLabel#cardSub {{ color: {theme['text_sec']}; background: transparent; border: none; }}
        """)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {theme['bg_ter']};
                border-radius: 2px; border: none;
            }}
            QProgressBar::chunk {{
                background-color: {theme['accent']};
                border-radius: 2px;
            }}
        """)

    def set_value(self, main_text: str, sub_text: str = "", progress: int = 0):
        self.value_label.setText(main_text)
        self.sub_label.setText(sub_text)
        self.progress_bar.setValue(max(0, min(100, progress)))


class StatsRow(QWidget):
    """4 张统计卡片行"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        self.cards = {}
        specs = [
            ("progress", "📚", "视频进度"),
            ("duration", "⏱", "累计时长"),
            ("today", "📅", "今日概览"),
            ("balance", "⚖", "学习余额"),
        ]
        for key, icon, title in specs:
            card = _StatCard(icon, title)
            self.cards[key] = card
            layout.addWidget(card, 1)

    def update_stats(self, **kwargs):
        for key, card in self.cards.items():
            if key in kwargs:
                card.set_value(*kwargs[key])



# ==================== 学习计划编辑弹窗 ====================

class PlanEditDialog(QDialog):
    """更改学习计划 — 模态编辑弹窗

    包含原学习计划卡片的所有编辑功能：
    - 开始日期选择器
    - 双页签：整体调节（预设 + 组滑块）/ 每日微调（7 个独立滑块）
    - 取消 / 确认更改 按钮
    """
    PRESETS: list[tuple[str, float]] = [
        ("清空", 0.0),
        ("0.5h/天", 0.5),
        ("1h/天", 1.0),
        ("2h/天", 2.0),
        ("3h/天", 3.0),
    ]

    PAGE_GROUP = 0
    PAGE_DAILY = 1

    def __init__(self, schedule: list, start_date_iso: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("更改学习计划")
        self.setModal(True)
        self.setMinimumWidth(680)
        self.setMinimumHeight(520)

        self._updating = False
        self._start_date_iso = start_date_iso

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 22, 28, 22)
        main_layout.setSpacing(14)

        # ---- 日期行 ----
        date_row = QHBoxLayout()
        date_row.setSpacing(10)
        date_icon = QLabel("📅 开始日期")
        date_icon.setFont(get_font("Regular", 12))
        date_icon.setObjectName("planTitle")
        date_row.addWidget(date_icon)
        self.date_picker = ElaDatePicker()
        self.date_picker.setFixedHeight(32)
        if start_date_iso:
            try:
                d = datetime.fromisoformat(start_date_iso).date()
                self.date_picker.setDate(QDate(d.year, d.month, d.day))
            except (ValueError, TypeError):
                self.date_picker.setDate(QDate.currentDate())
        else:
            self.date_picker.setDate(QDate.currentDate())
        self.date_picker.dateChanged.connect(self._on_date_changed)
        date_row.addWidget(self.date_picker)
        date_row.addStretch()
        main_layout.addLayout(date_row)

        # ---- 页签切换按钮 ----
        tab_row = QHBoxLayout()
        tab_row.setSpacing(8)
        self.btn_group = QPushButton("🎯 整体调节")
        self.btn_group.setCheckable(True)
        self.btn_group.setChecked(True)
        self.btn_group.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_group.setFont(get_font("Bold", 11))
        self.btn_group.setFixedHeight(30)
        self.btn_group.clicked.connect(lambda: self._switch_page(self.PAGE_GROUP))
        tab_row.addWidget(self.btn_group)

        self.btn_daily = QPushButton("📋 每日微调")
        self.btn_daily.setCheckable(True)
        self.btn_daily.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_daily.setFont(get_font("Bold", 11))
        self.btn_daily.setFixedHeight(30)
        self.btn_daily.clicked.connect(lambda: self._switch_page(self.PAGE_DAILY))
        tab_row.addWidget(self.btn_daily)
        tab_row.addStretch()
        main_layout.addLayout(tab_row)

        # ---- 双页签内容 ----
        self.stack = QStackedWidget()
        self.stack.setObjectName("planStack")

        # --- 页签 1：整体调节 ---
        page_group = QWidget()
        pg_layout = QVBoxLayout(page_group)
        pg_layout.setContentsMargins(0, 6, 0, 0)
        pg_layout.setSpacing(10)

        # 预设方案
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        preset_icon = QLabel("📦 预设方案")
        preset_icon.setFont(get_font("Regular", 12))
        preset_icon.setObjectName("fieldLabel")
        preset_row.addWidget(preset_icon)

        self._preset_buttons: list[QPushButton] = []
        for label, hours in self.PRESETS:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(get_font("Medium", 10))
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, h=hours: self._apply_preset(h))
            self._preset_buttons.append(btn)
            preset_row.addWidget(btn)
        preset_row.addStretch()
        pg_layout.addLayout(preset_row)

        # 工作日组滑块
        wd_row = QHBoxLayout()
        wd_row.setSpacing(12)
        wd_icon = QLabel("🎯 工作日")
        wd_icon.setFont(get_font("Regular", 12))
        wd_icon.setObjectName("fieldLabel")
        wd_row.addWidget(wd_icon)

        self.weekday_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.weekday_slider.setRange(0, 72)
        self.weekday_slider.setSingleStep(3)
        self.weekday_slider.setPageStep(6)
        self.weekday_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.weekday_slider.setFixedHeight(28)
        self.weekday_slider.valueChanged.connect(self._on_weekday_change)
        wd_row.addWidget(self.weekday_slider, 1)

        self.weekday_value_label = QLabel("0.0 小时/天")
        self.weekday_value_label.setFont(get_font("Bold", 12))
        self.weekday_value_label.setObjectName("groupValue")
        self.weekday_value_label.setMinimumWidth(85)
        self.weekday_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        wd_row.addWidget(self.weekday_value_label)

        wd_hint = QLabel("周一至周五")
        wd_hint.setFont(get_font("Regular", 10))
        wd_hint.setObjectName("groupHint")
        wd_row.addWidget(wd_hint)
        pg_layout.addLayout(wd_row)

        # 周末组滑块
        we_row = QHBoxLayout()
        we_row.setSpacing(12)
        we_icon = QLabel("🎯 周末")
        we_icon.setFont(get_font("Regular", 12))
        we_icon.setObjectName("fieldLabel")
        we_row.addWidget(we_icon)

        self.weekend_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.weekend_slider.setRange(0, 72)
        self.weekend_slider.setSingleStep(3)
        self.weekend_slider.setPageStep(6)
        self.weekend_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.weekend_slider.setFixedHeight(28)
        self.weekend_slider.valueChanged.connect(self._on_weekend_change)
        we_row.addWidget(self.weekend_slider, 1)

        self.weekend_value_label = QLabel("0.0 小时/天")
        self.weekend_value_label.setFont(get_font("Bold", 12))
        self.weekend_value_label.setObjectName("groupValue")
        self.weekend_value_label.setMinimumWidth(85)
        self.weekend_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        we_row.addWidget(self.weekend_value_label)

        we_hint = QLabel("周六至周日")
        we_hint.setFont(get_font("Regular", 10))
        we_hint.setObjectName("groupHint")
        we_row.addWidget(we_hint)
        pg_layout.addLayout(we_row)

        pg_layout.addStretch()
        self.stack.addWidget(page_group)  # index 0

        # --- 页签 2：每日微调 ---
        page_daily = QWidget()
        pd_layout = QVBoxLayout(page_daily)
        pd_layout.setContentsMargins(0, 6, 0, 0)
        pd_layout.setSpacing(6)

        daily_hint = QLabel("拖动下方滑块独立调整每天的学习时长")
        daily_hint.setFont(get_font("Regular", 10))
        daily_hint.setObjectName("customTitle")
        pd_layout.addWidget(daily_hint)

        self._day_sliders: list[ClickableSlider] = []
        self._day_value_labels: list[QLabel] = []
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for i, day_name in enumerate(day_names):
            row = QHBoxLayout()
            row.setSpacing(12)

            day_label = QLabel(day_name)
            day_label.setFont(get_font("Bold", 11))
            day_label.setObjectName("dayName")
            day_label.setFixedWidth(36)
            day_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(day_label)

            slider = ClickableSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 72)
            slider.setSingleStep(3)
            slider.setPageStep(6)
            slider.setCursor(Qt.CursorShape.PointingHandCursor)
            slider.setFixedHeight(24)
            slider.valueChanged.connect(lambda v, idx=i: self._on_day_change(idx, v))
            row.addWidget(slider, 1)
            self._day_sliders.append(slider)

            value_label = QLabel("0h")
            value_label.setFont(get_font("Bold", 12))
            value_label.setObjectName("dayValue")
            value_label.setFixedWidth(40)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(value_label)
            self._day_value_labels.append(value_label)

            pd_layout.addLayout(row)

        pd_layout.addStretch()
        self.stack.addWidget(page_daily)  # index 1

        self.stack.setCurrentIndex(self.PAGE_GROUP)
        main_layout.addWidget(self.stack, 1)

        # ---- 底部按钮 ----
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setFixedHeight(34)
        self.btn_cancel.setMinimumWidth(80)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setFont(get_font("Medium", 11))
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        self.btn_confirm = QPushButton("确认更改")
        self.btn_confirm.setFixedHeight(34)
        self.btn_confirm.setMinimumWidth(100)
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.setFont(get_font("Bold", 11))
        self.btn_confirm.setDefault(True)
        self.btn_confirm.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_confirm)

        main_layout.addLayout(btn_row)

        # ---- 初始化滑块值 ----
        self._init_values(schedule)

        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_manager.get_theme())

    # ==================== 公共接口 ====================

    def get_plan(self) -> tuple:
        """返回 (schedule_list[7], start_date_iso)"""
        return ([s.value() / 6.0 for s in self._day_sliders], self._start_date_iso)

    # ==================== 内部初始化 ====================

    def _init_values(self, schedule: list):
        """用传入的 schedule 数据初始化所有滑块"""
        self._updating = True
        for slider, val in zip(self._day_sliders, schedule):
            slider.blockSignals(True)
            slider.setValue(min(int(float(val) * 6), 72))
            slider.blockSignals(False)

        self.weekday_slider.blockSignals(True)
        self.weekday_slider.setValue(min(int(float(schedule[0]) * 6), 72))
        self.weekday_slider.blockSignals(False)
        self.weekend_slider.blockSignals(True)
        self.weekend_slider.setValue(min(int(float(schedule[5]) * 6), 72))
        self.weekend_slider.blockSignals(False)

        self._update_all_labels()
        self._updating = False

    # ==================== 页签切换 ====================

    def _switch_page(self, page: int):
        self.stack.setCurrentIndex(page)
        self.btn_group.setChecked(page == self.PAGE_GROUP)
        self.btn_daily.setChecked(page == self.PAGE_DAILY)

    # ==================== 日期 ====================

    def _on_date_changed(self, qdate: QDate):
        if self._updating:
            return
        self._start_date_iso = qdate.toString(Qt.DateFormat.ISODate)

    # ==================== 预设 ====================

    def _apply_preset(self, hours_per_day: float):
        if self._updating:
            return
        self._updating = True

        val = int(hours_per_day * 6)
        for slider in self._day_sliders:
            slider.blockSignals(True)
            slider.setValue(val)
            slider.blockSignals(False)

        self.weekday_slider.blockSignals(True)
        self.weekday_slider.setValue(val)
        self.weekday_slider.blockSignals(False)
        self.weekend_slider.blockSignals(True)
        self.weekend_slider.setValue(val)
        self.weekend_slider.blockSignals(False)

        self._update_all_labels()
        self._updating = False

    # ==================== 组滑块（页签 1） ====================

    def _on_weekday_change(self, val: int):
        if self._updating:
            return
        self._updating = True
        for i in range(5):
            self._day_sliders[i].blockSignals(True)
            self._day_sliders[i].setValue(val)
            self._day_sliders[i].blockSignals(False)
        self._updating = False
        self._update_all_labels()

    def _on_weekend_change(self, val: int):
        if self._updating:
            return
        self._updating = True
        for i in range(5, 7):
            self._day_sliders[i].blockSignals(True)
            self._day_sliders[i].setValue(val)
            self._day_sliders[i].blockSignals(False)
        self._updating = False
        self._update_all_labels()

    # ==================== 每日滑块（页签 2） ====================

    def _on_day_change(self, idx: int, val: int):
        if self._updating:
            return
        self._updating = True
        if idx == 0:
            self.weekday_slider.blockSignals(True)
            self.weekday_slider.setValue(val)
            self.weekday_slider.blockSignals(False)
        elif idx == 5:
            self.weekend_slider.blockSignals(True)
            self.weekend_slider.setValue(val)
            self.weekend_slider.blockSignals(False)
        self._updating = False
        self._update_all_labels()

    # ==================== 标签刷新 ====================

    def _update_all_labels(self):
        """刷新所有滑块的值标签"""
        for slider, label in zip(self._day_sliders, self._day_value_labels):
            hours = slider.value() / 6.0
            label.setText(f"{int(hours)}h" if hours == int(hours) else f"{hours:.1f}h")
        self._update_group_labels()

    def _update_group_labels(self):
        """刷新组滑块的值标签"""
        wd = self.weekday_slider.value() / 6.0
        we = self.weekend_slider.value() / 6.0
        self.weekday_value_label.setText(f"{wd:.1f} 小时/天")
        self.weekend_value_label.setText(f"{we:.1f} 小时/天")

    # ==================== 主题 ====================

    def _apply_theme(self, theme: dict):
        self.setStyleSheet(f"""
            PlanEditDialog {{
                background-color: {theme['bg_sec']};
                border: 1px solid {theme['border']};
                border-radius: 12px;
            }}
            QLabel#planTitle {{
                color: {theme['text_main']}; background: transparent; border: none;
                font-weight: bold; font-size: 13px;
            }}
            QLabel#fieldLabel {{
                color: {theme['text_sec']}; background: transparent; border: none;
                font-size: 12px;
            }}
            QLabel#groupValue {{
                color: {theme['accent']}; background: transparent; border: none;
                font-weight: bold; font-size: 12px;
            }}
            QLabel#groupHint {{
                color: {theme['text_sec']}; background: transparent; border: none;
                font-size: 10px;
            }}
            QLabel#dayName {{
                color: {theme['text_main']}; background: transparent; border: none;
                font-size: 11px;
            }}
            QLabel#dayValue {{
                color: {theme['accent']}; background: transparent; border: none;
                font-size: 12px;
            }}
            QLabel#customTitle {{
                color: {theme['text_sec']}; background: transparent; border: none;
                font-size: 10px; font-style: italic;
            }}
            #planStack {{ background: transparent; border: none; }}
        """)

        # 水平滑块统一样式
        h_slider_qss = f"""
            QSlider::groove:horizontal {{
                background: {theme['bg_ter']}; height: 6px; border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme['accent']};
                border-top-left-radius: 3px; border-bottom-left-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {theme['accent']}; width: 16px; height: 16px;
                border-radius: 8px; margin: -5px 0px; border: none;
            }}
        """
        self.weekday_slider.setStyleSheet(h_slider_qss)
        self.weekend_slider.setStyleSheet(h_slider_qss)
        for slider in self._day_sliders:
            slider.setStyleSheet(h_slider_qss)

        # 页签切换按钮
        tab_active = f"""
            QPushButton {{
                background-color: {theme['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 4px 14px;
                font-size: 11px;
            }}
        """
        tab_inactive = f"""
            QPushButton {{
                background-color: {theme['bg_ter']};
                color: {theme['text_sec']};
                border: none;
                border-radius: 8px;
                padding: 4px 14px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {theme['text_main']};
            }}
        """
        self.btn_group.setStyleSheet(tab_active if self.btn_group.isChecked() else tab_inactive)
        self.btn_daily.setStyleSheet(tab_inactive if self.btn_group.isChecked() else tab_active)

        # 预设按钮
        preset_qss = f"""
            QPushButton {{
                background-color: {theme['bg_ter']};
                color: {theme['text_sec']};
                border: 1px solid {theme['border']};
                border-radius: 6px;
                padding: 3px 10px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {theme['border']};
                color: {theme['text_main']};
            }}
        """
        for btn in self._preset_buttons:
            btn.setStyleSheet(preset_qss)

        # 底部按钮
        cancel_qss = f"""
            QPushButton {{
                background-color: {theme['bg_ter']};
                color: {theme['text_sec']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
                padding: 6px 18px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {theme['text_main']};
                border-color: {theme['text_sec']};
            }}
        """
        self.btn_cancel.setStyleSheet(cancel_qss)

        confirm_qss = f"""
            QPushButton {{
                background-color: {theme['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 20px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {theme['text_main']};
            }}
        """
        self.btn_confirm.setStyleSheet(confirm_qss)


# ==================== 学习计划卡片 ====================

class StudyPlanCard(QWidget):
    """学习计划卡片 — 只读展示 + 弹窗编辑

    卡片以只读模式展示当前学习计划核心信息：
    - 开始日期（文本）
    - 7 天每日时长可视化（迷你进度条）
    - 每周合计
    - 预计完成 + 学习余额结果卡片
    - 学习建议

    点击「更改学习计划」按钮弹出 PlanEditDialog 进行编辑。
    """
    plan_changed = Signal(list, str)  # (schedule_list[7], start_date_iso)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StudyPlanCard")

        self._schedule: list[float] = [0.0] * 7
        self._start_date_iso: str = ""
        self._balance_hours: float = 0.0
        self._is_completed: bool = False
        self._estimated_finish: str = "--"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 22)
        main_layout.setSpacing(14)

        # ========== 标题行 ==========
        header = QHBoxLayout()
        header.setSpacing(12)
        title = QLabel("📋 学习计划")
        title.setFont(get_font("Bold", 13))
        title.setObjectName("planTitle")
        header.addWidget(title)
        header.addStretch()

        self.btn_change = QPushButton("✏️ 更改学习计划")
        self.btn_change.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_change.setFont(get_font("Medium", 11))
        self.btn_change.setFixedHeight(32)
        self.btn_change.clicked.connect(self._on_change_clicked)
        header.addWidget(self.btn_change)
        main_layout.addLayout(header)

        # ========== 开始日期（只读文本） ==========
        self.date_display = QLabel("📅 开始日期：未设置")
        self.date_display.setFont(get_font("Regular", 12))
        self.date_display.setObjectName("dateDisplay")
        main_layout.addWidget(self.date_display)

        # ========== 每日时长可视化 ==========
        daily_container = QFrame()
        daily_container.setObjectName("DailyBarsContainer")
        daily_layout = QHBoxLayout(daily_container)
        daily_layout.setContentsMargins(20, 14, 20, 14)
        daily_layout.setSpacing(8)

        self._day_bars: list[QProgressBar] = []
        self._day_value_labels: list[QLabel] = []
        self._day_name_labels: list[QLabel] = []
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for name in day_names:
            col = QVBoxLayout()
            col.setSpacing(3)
            col.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            name_label = QLabel(name)
            name_label.setFont(get_font("Bold", 10))
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setObjectName("dayBarName")
            col.addWidget(name_label)
            self._day_name_labels.append(name_label)

            bar = QProgressBar()
            bar.setRange(0, 120)  # 0–12h, 步长 0.1h
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            bar.setMinimumWidth(50)
            bar.setObjectName("dayBar")
            col.addWidget(bar)
            self._day_bars.append(bar)

            value_label = QLabel("0h")
            value_label.setFont(get_font("Bold", 12))
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_label.setObjectName("dayBarValue")
            col.addWidget(value_label)
            self._day_value_labels.append(value_label)

            daily_layout.addLayout(col)

        main_layout.addWidget(daily_container)

        # ========== 每周合计 ==========
        self.weekly_total_label = QLabel("📊 每周合计：0.0 小时")
        self.weekly_total_label.setFont(get_font("Regular", 12))
        self.weekly_total_label.setObjectName("weeklyTotal")
        main_layout.addWidget(self.weekly_total_label)

        # ========== 结果卡片（同现有逻辑） ==========
        results_row = QHBoxLayout()
        results_row.setSpacing(16)

        self.finish_card, self._result_finish_value, self._result_finish_sub = \
            self._make_result_card("🏁", "预计完成")
        results_row.addWidget(self.finish_card, 1)

        self.balance_card, self._result_balance_value, self._result_balance_sub = \
            self._make_result_card("⚖", "学习余额")
        results_row.addWidget(self.balance_card, 1)
        main_layout.addLayout(results_row)

        # ========== 学习建议 ==========
        self.suggestion_label = QLabel("")
        self.suggestion_label.setFont(get_font("Regular", 10))
        self.suggestion_label.setWordWrap(True)
        self.suggestion_label.setObjectName("suggestionLabel")
        main_layout.addWidget(self.suggestion_label)

        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_manager.get_theme())

    # ==================== 结果卡片工厂 ====================

    def _make_result_card(self, icon: str, title: str) -> tuple[QFrame, QLabel, QLabel]:
        card = QFrame()
        card.setObjectName("ResultCard")
        card.setMinimumHeight(72)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(2)

        header = QHBoxLayout()
        header.setSpacing(4)
        icon_lbl = QLabel(icon)
        header.addWidget(icon_lbl)
        title_lbl = QLabel(title)
        title_lbl.setFont(get_font("Regular", 10))
        title_lbl.setObjectName("resultTitle")
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        value_lbl = QLabel("--")
        value_lbl.setFont(get_font("Bold", 18))
        value_lbl.setObjectName("resultValue")
        layout.addWidget(value_lbl)

        sub_lbl = QLabel("")
        sub_lbl.setFont(get_font("Regular", 9))
        sub_lbl.setObjectName("resultSub")
        layout.addWidget(sub_lbl)

        return card, value_lbl, sub_lbl

    # ==================== 公共接口 ====================

    def get_plan(self) -> tuple:
        """返回 (schedule_list[7], start_date_iso)"""
        return (list(self._schedule), self._start_date_iso)

    def set_data(self, schedule: list, start_date_iso: str,
                 balance_hours: float = 0.0, is_completed: bool = False,
                 estimated_finish: str = "--"):
        """更新卡片只读展示数据"""
        self._schedule = [float(v) for v in schedule]
        self._start_date_iso = start_date_iso
        self._balance_hours = balance_hours
        self._is_completed = is_completed
        self._estimated_finish = estimated_finish

        # 更新日期显示
        if start_date_iso:
            try:
                d = datetime.fromisoformat(start_date_iso).date()
                # 中文日期格式
                self.date_display.setText(f"📅 开始日期：{d.year}年{d.month}月{d.day}日")
            except (ValueError, TypeError):
                self.date_display.setText("📅 开始日期：未设置")
        else:
            self.date_display.setText("📅 开始日期：未设置")

        # 更新每日进度条
        for i, hours in enumerate(self._schedule):
            bar_val = min(int(hours * 10), 120)
            self._day_bars[i].setValue(bar_val)
            h = self._schedule[i]
            self._day_value_labels[i].setText(
                f"{int(h)}h" if h == int(h) else f"{h:.1f}h"
            )

        # 更新每周合计
        weekly = sum(self._schedule)
        self.weekly_total_label.setText(f"📊 每周合计：{weekly:.1f} 小时")

        # 更新结果卡片和建议
        self._update_result_cards()
        self._update_suggestion()

    # ==================== 编辑弹窗 ====================

    def _on_change_clicked(self):
        """打开更改学习计划弹窗"""
        dialog = PlanEditDialog(self._schedule, self._start_date_iso, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_schedule, new_date = dialog.get_plan()
            self.plan_changed.emit(new_schedule, new_date)

    # ==================== 结果卡片 ====================

    def _update_result_cards(self):
        theme = theme_manager.get_theme()
        weekly = sum(self._schedule)

        if self._is_completed:
            self._result_finish_value.setText("已完成")
            self._result_finish_sub.setText("🎉 所有视频已学完")
        elif not self._start_date_iso or weekly < 0.01:
            self._result_finish_value.setText("--")
            self._result_finish_sub.setText("设置日期和目标后可查看")
        else:
            self._result_finish_value.setText(self._estimated_finish)
            try:
                finish_dt = datetime.fromisoformat(self._estimated_finish).date()
                remaining = (finish_dt - date.today()).days
                if remaining > 0:
                    self._result_finish_sub.setText(f"剩余约 {remaining} 天")
                elif remaining == 0:
                    self._result_finish_sub.setText("预计今日完成")
                else:
                    self._result_finish_sub.setText("已超出预计日期")
            except (ValueError, TypeError):
                self._result_finish_sub.setText("")

        self._result_finish_value.setStyleSheet(
            f"color: {theme['text_main']}; font-weight: bold; font-size: 18px;"
            f"background: transparent; border: none;"
        )

        if self._is_completed:
            self._result_balance_value.setText("已完成")
            self._result_balance_sub.setText("🎉 恭喜完成课程")
            bal_color = "#4CAF50"
        elif not self._start_date_iso or weekly < 0.01:
            self._result_balance_value.setText("--")
            self._result_balance_sub.setText("设置日期和目标后可查看")
            bal_color = theme["text_sec"]
        else:
            sign = "+" if self._balance_hours >= 0 else ""
            self._result_balance_value.setText(f"{sign}{self._balance_hours:.1f}h")
            if self._balance_hours >= 0:
                self._result_balance_sub.setText("超前于计划")
                bal_color = "#4CAF50"
            elif self._balance_hours > -1:
                self._result_balance_sub.setText("接近计划")
                bal_color = theme["accent"]
            else:
                self._result_balance_sub.setText("落后于计划")
                bal_color = theme["danger"]

        self._result_balance_value.setStyleSheet(
            f"color: {bal_color}; font-weight: bold; font-size: 18px;"
            f"background: transparent; border: none;"
        )

    # ==================== 学习建议 ====================

    def _update_suggestion(self):
        weekly = sum(self._schedule)

        if self._is_completed:
            self.suggestion_label.setText("🎉 恭喜完成！可以开始新课程了")
        elif not self._start_date_iso:
            self.suggestion_label.setText("💡 请点击「更改学习计划」设置开始日期和目标")
        elif weekly < 0.01:
            self.suggestion_label.setText("💡 请点击「更改学习计划」设置每周学习时长")
        elif self._balance_hours < -5:
            try:
                start_dt = datetime.fromisoformat(self._start_date_iso).date()
                elapsed = max(1, (date.today() - start_dt).days)
                extra_per_week = abs(self._balance_hours) / elapsed * 7
                self.suggestion_label.setText(
                    f"⚠ 落后较多，建议每周多学 {extra_per_week:.1f}h 可赶上")
            except (ValueError, TypeError):
                self.suggestion_label.setText("⚠ 落后较多，请检查学习节奏")
        elif self._balance_hours < -1:
            self.suggestion_label.setText("📌 稍有落后，保持当前节奏即可追上")
        elif self._balance_hours < 0:
            self.suggestion_label.setText("👍 接近计划，继续加油")
        else:
            self.suggestion_label.setText("✅ 超前于计划，保持节奏！")

    # ==================== 主题 ====================

    def _apply_theme(self, theme: dict):
        self.setStyleSheet(f"""
            #StudyPlanCard {{
                background-color: {theme['bg_sec']};
                border: 1px solid {theme['border']};
                border-radius: 12px;
            }}
            QLabel#planTitle {{
                color: {theme['text_main']}; background: transparent; border: none;
                font-weight: bold; font-size: 13px;
            }}
            QLabel#dateDisplay {{
                color: {theme['text_sec']}; background: transparent; border: none;
                font-size: 12px;
            }}
            QLabel#dayBarName {{
                color: {theme['text_sec']}; background: transparent; border: none;
                font-size: 10px;
            }}
            QLabel#dayBarValue {{
                color: {theme['text_main']}; background: transparent; border: none;
                font-size: 12px;
            }}
            QLabel#weeklyTotal {{
                color: {theme['text_sec']}; background: transparent; border: none;
                font-size: 12px;
            }}
            QLabel#suggestionLabel {{
                color: {theme['text_sec']}; background: transparent; border: none;
                font-style: italic; padding-top: 4px; font-size: 10px;
            }}
            QFrame#DailyBarsContainer {{
                background-color: {theme['bg_ter']};
                border: 1px solid {theme['border']};
                border-radius: 10px;
            }}
            QFrame#ResultCard {{
                background-color: {theme['bg_ter']};
                border: 1px solid {theme['border']};
                border-radius: 10px;
            }}
            QLabel#resultTitle {{
                color: {theme['text_sec']}; background: transparent; border: none;
            }}
            QLabel#resultValue {{
                background: transparent; border: none;
            }}
            QLabel#resultSub {{
                color: {theme['text_sec']}; background: transparent; border: none;
            }}
        """)

        # 每日进度条样式
        bar_qss = f"""
            QProgressBar {{
                background-color: {theme['bg_main']};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {theme['accent']};
                border-radius: 5px;
            }}
        """
        for bar in self._day_bars:
            bar.setStyleSheet(bar_qss)

        # 更改按钮
        self.btn_change.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['bg_ter']};
                color: {theme['accent']};
                border: 1px solid {theme['accent']};
                border-radius: 8px;
                padding: 4px 16px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
                color: white;
            }}
        """)

        self._update_result_cards()

# ==================== 课程看板主视图 ====================

class PropertiesView(QWidget):
    """课程看板"""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._course_id = None
        self._refreshing = False

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        self.scroll_area.setWidget(self.container)
        outer_layout.addWidget(self.scroll_area)

        # 第 1 行：4 张统计卡片
        self.stats_row = StatsRow()
        self.layout.addWidget(self.stats_row)

        # 第 2 行：学习计划卡片（日期 + 周计划 + 建议）
        self.study_plan = StudyPlanCard()
        self.study_plan.plan_changed.connect(self._on_plan_changed)
        self.layout.addWidget(self.study_plan)

        # 第 3 行：学习时间线（纯可视化）
        self.timeline = CourseTimeline()
        self.layout.addWidget(self.timeline)

        self.layout.addStretch()

        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_manager.get_theme())

    def set_course_id(self, course_id: str):
        self._course_id = course_id

    def load_course(self, course_id: str):
        self._course_id = course_id
        self._refresh_all()

    def _refresh_all(self):
        if not self._course_id or self._refreshing:
            return
        self._refreshing = True
        try:
            data = self.controller.get_dashboard_data(self._course_id)

            self.stats_row.update_stats(
                progress=(
                    f"{data.completed_videos}/{data.total_videos}",
                    f"{data.total_videos - data.completed_videos} 个待完成",
                    int(data.completed_videos / max(1, data.total_videos) * 100),
                ),
                duration=(
                    f"{data.watched_hours:.1f}h",
                    f"共 {data.total_hours:.1f}h",
                    int(data.watched_hours / max(0.01, data.total_hours) * 100),
                ),
                today=(
                    f"{data.today_hours:.1f}h",
                    f"计划 {data.plan_today_hours:.1f}h",
                    int(data.today_hours / max(0.01, data.plan_today_hours) * 100) if data.plan_today_hours > 0 else 0,
                ),
                balance=(
                    f"+{data.balance_hours:.1f}h" if data.balance_hours >= 0 else f"{data.balance_hours:.1f}h",
                    "超前于计划" if data.balance_hours >= 0 else "落后于计划",
                    -1,
                ),
            )
            theme = theme_manager.get_theme()
            bal_color = "#4CAF50" if data.balance_hours >= 0 else theme["danger"]
            self.stats_row.cards["balance"].value_label.setStyleSheet(
                f"color: {bal_color}; font-size: 20px; font-weight: bold; background: transparent; border: none;")

            # 学习计划卡片 - blockSignals 防循环
            is_completed = (data.estimated_finish_str == "已完成")
            self.study_plan.blockSignals(True)
            self.study_plan.set_data(
                data.weekly_schedule,
                data.start_date_iso or "",
                data.balance_hours,
                is_completed,
                data.estimated_finish_str,
            )
            self.study_plan.blockSignals(False)

            # 时间线（纯可视化，无需 blockSignals）
            self.timeline.set_data(
                start_date_iso=data.start_date_iso,
                estimated_finish=data.estimated_finish_str,
                balance_hours=data.balance_hours,
                progress_pct=int(data.completed_videos / max(1, data.total_videos) * 100),
                total_videos=data.total_videos,
                completed_videos=data.completed_videos,
            )
        finally:
            self._refreshing = False

    def _on_plan_changed(self, schedule: list, start_date_iso: str):
        """统一处理：StudyPlanCard 中日期或周计划变更"""
        if not self._course_id or self._refreshing:
            return
        self.controller.set_weekly_schedule(self._course_id, schedule, start_date_iso)
        self._refresh_all()

    def _apply_theme(self, theme):
        self.setStyleSheet(f"background-color: {theme['bg_main']};")
        # scroll_area 的 viewport 必须在 frame 之下保持透明
        vp = self.scroll_area.viewport()
        vp.setStyleSheet(f"background-color: transparent;")
        self.scroll_area.setStyleSheet(
            self._scrollbar_qss().replace(
                "QScrollArea {",
                f"QScrollArea {{ border: none; background-color: {theme['bg_main']}; "
                f"border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; "))
        self.container.setStyleSheet(f"background-color: transparent;")

    def _scrollbar_qss(self) -> str:
        theme = theme_manager.get_theme()
        return f"""
            QScrollArea {{ border: none; background-color: transparent; }}
            QScrollBar:vertical {{
                background: transparent; width: 4px; margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['accent']}; min-height: 20px; border-radius: 2px; margin: 0px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {theme['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """
