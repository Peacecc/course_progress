from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QFrame, QDoubleSpinBox, QPushButton, QDateEdit, 
                             QSlider, QCheckBox, QSizePolicy, QStyleOptionSlider, QStyle, QScrollArea)
from PySide6.QtCore import Qt, QDate, Signal, QPoint
from PySide6.QtGui import QPainter, QBrush, QColor
from services.theme_service import theme_service as theme_manager
from models.data_manager import DataManager
from datetime import datetime, timedelta, date

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            val = self.pixelPosToRangeValue(event.position().toPoint())
            self.setValue(val)
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            val = self.pixelPosToRangeValue(event.position().toPoint())
            self.setValue(val)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def pixelPosToRangeValue(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
        sr = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderHandle, self)

        if self.orientation() == Qt.Orientation.Vertical:
            sliderLength = sr.height()
            sliderMin = gr.y()
            sliderMax = gr.y() + gr.height() - sliderLength + 1
            prop = 1.0 - (pos.y() - sliderMin) / (sliderMax - sliderMin)
        else:
            sliderLength = sr.width()
            sliderMin = gr.x()
            sliderMax = gr.x() + gr.width() - sliderLength + 1
            prop = (pos.x() - sliderMin) / (sliderMax - sliderMin)

        return int(self.minimum() + prop * (self.maximum() - self.minimum()))

class DailySlider(QWidget):
    value_changed = Signal(float)

    def __init__(self, day_name, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignHCenter) 
        
        # Top Label (Value)
        self.val_label = QLabel("0h")
        self.val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.val_label, 0, Qt.AlignmentFlag.AlignHCenter)
        
        # Slider
        self.slider = ClickableSlider(Qt.Orientation.Vertical)
        self.slider.setRange(0, 72) # 0 to 12h
        self.slider.setSingleStep(1)
        self.slider.setPageStep(6)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setInvertedAppearance(False) # Ensure Bottom is 0, Top is Max
        self.slider.valueChanged.connect(self.on_slider_change)
        
        # Important: Fixed height for sliders to look uniform
        self.slider.setFixedHeight(120)
        self.layout.addWidget(self.slider, 0, Qt.AlignmentFlag.AlignHCenter)
        
        # Day Name
        self.day_label = QLabel(day_name)
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.day_label, 0, Qt.AlignmentFlag.AlignHCenter)
        
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(theme_manager.get_theme())

    def on_slider_change(self, val):
        minutes = val * 10
        hours_val = minutes / 60
            
        h = int(hours_val)
        m = int(minutes % 60)
        
        if m == 0:
            self.val_label.setText(f"{h}h")
        else:
            self.val_label.setText(f"{h}h{m}")
            
        self.value_changed.emit(hours_val)

    def set_value(self, hours):
        val = int(hours * 6)
        if val > 72: val = 72
        self.slider.setValue(val)

    def get_value(self):
        return self.slider.value() / 6.0
    
    def set_locked(self, locked):
        self.slider.setEnabled(not locked)

    def apply_theme(self, theme):
        self.val_label.setStyleSheet(f"background: transparent; color: {theme['accent']}; font-weight: bold; font-size: 11px;")
        self.day_label.setStyleSheet(f"background: transparent; color: {theme['text_main']}; font-size: 12px;") 
        
        # Refined Slider Style (Thermometer Strategy)
        # To fix artifacts where the Bar meets the Round Handle:
        # 1. Sub-page top is FLAT (radius 0). Bottom is ROUND.
        # 2. Handle is CIRCLE.
        # 3. Handle sits on top of the flat sub-page end, creating a perfect continuous capsule.
        self.slider.setStyleSheet(f"""
            QSlider::groove:vertical {{
                background: {theme['bg_ter']};
                width: 16px; 
                border-radius: 8px;
            }}
            QSlider::sub-page:vertical {{
                background: {theme['accent']};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
            }}
            QSlider::add-page:vertical {{
                background: transparent;
                border-radius: 8px;
            }}
            QSlider::handle:vertical {{
                background: {theme['accent']};
                height: 16px; 
                width: 16px;
                border-radius: 8px;
                margin: 0px; 
                border: none;
            }}
            QSlider::sub-page:vertical:disabled {{
                background: {theme['text_sec']};
            }}
            QSlider::handle:vertical:disabled {{
                background: {theme['text_sec']};
            }}
        """)

class DashboardCard(QFrame):
    """
    Base Card Class for unified styling.
    Has a Title Header and a Content Area.
    """
    def __init__(self, title, icon="", parent=None, header_controls=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Outer margins handled by parent layout spacing? No, card has concise internal
        self.main_layout.setSpacing(0)
        
        # Header
        self.header_frame = QWidget()
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(20, 15, 20, 10)
        self.header_layout.setSpacing(10)
        
        # Icon + Title
        full_title = f"{icon} {title}" if icon else title
        self.title_label = QLabel(full_title)
        self.title_label.setObjectName("CardTitle")
        self.header_layout.addWidget(self.title_label)
        
        self.header_layout.addStretch()
        
        # Optional Controls in Header
        if header_controls:
            for c in header_controls:
                self.header_layout.addWidget(c)
                
        self.main_layout.addWidget(self.header_frame)
        
        # Divider? Optional. Let's start without.
        
        # Content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.setSpacing(15)
        self.main_layout.addWidget(self.content_widget)
        
        theme_manager.theme_changed.connect(self.apply_theme)
        
    def apply_theme(self, theme):
        self.setStyleSheet(f"""
            DashboardCard {{
                background-color: {theme['bg_sec']};
                border-radius: 12px;
                border: 1px solid {theme['border']};
            }}
            QLabel#CardTitle {{
                color: {theme['text_main']};
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }}
        """)


class CourseHeatMap(DashboardCard):
    def __init__(self, parent=None):
        super().__init__("学习投入热力图", "🔥", parent)
        self.daily_stats = {}
        self.target = 1.0 
        
        self.heatmap_area = QWidget()
        self.heatmap_area.setMinimumHeight(120) 
        self.content_layout.addWidget(self.heatmap_area)

    def set_data(self, daily_stats, target_hours):
        self.daily_stats = daily_stats
        self.target = target_hours if target_hours > 0 else 1.0
        self.heatmap_area.update()
        
    def resizeEvent(self, event):
        self.heatmap_area.update()
        super().resizeEvent(event) # Card resize

    # Move paint to the inner widget
    # But wait, DashboardCard structure uses widget. We need to install EventFilter or subclass widget.
    # Simpler: Subclass DashboardCard but paint on content_widget? Or just custom widget inside.
    # Let's make heatmap_area a custom class OR use event filter.
    # Custom class is cleaner.
    
    # Actually, let's just make HeatmapArea widget inline here
    
        self.heatmap_area.paintEvent = self.paint_heatmap
        
    def paint_heatmap(self, event):
        painter = QPainter(self.heatmap_area)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        theme = theme_manager.get_theme()
        
        # Calculate Layout
        w = self.heatmap_area.width()
        h = self.heatmap_area.height()
        
        today = date.today()
        months_to_show = 12
        start_month = today.replace(day=1)
        for _ in range(months_to_show - 1):
            first = start_month.replace(day=1)
            prev = first - timedelta(days=1)
            start_month = prev.replace(day=1)
            
        gap_x = 8
        # Try to fit 12 blocks
        # block_width * 12 + 11 * 8 = w
        block_width = (w - (months_to_show - 1) * gap_x) / months_to_show
        
        cell_gap = 2
        # A block is 7 cells vertical? No, Heatmap is usually Week(Col) x Day(Row)? or Day(Col) x Week(Row)?
        # Our previous implementation: 
        # Left-Right = Weeks/Blocks.
        # Vertical = Days (Mon-Sun).
        # So width of block depends on how many weeks in that month. Usually 4-6.
        # Fixed cell size looks better than stretchy.
        
        cell_size = 10
        # Check if we can fit?
        # If w is large, centered.
        
        # Max width needed approx: 12 * (5*12) approx 800px.
        start_x = 0
        start_y = 10
        
        base_color = QColor(theme['bg_ter'])
        c1 = QColor(theme['accent']); c1.setAlpha(60)
        c2 = QColor(theme['accent']); c2.setAlpha(120)
        c3 = QColor(theme['accent']); c3.setAlpha(180)
        c4 = QColor(theme['accent'])
        
        current_m = start_month
        
        for i in range(months_to_show):
            # Month Label
            month_str = current_m.strftime("%Y-%m")
            painter.setPen(QColor(theme['text_sec']))
            font = painter.font(); font.setPointSize(8); painter.setFont(font)
            
            # Position: relative to block
            # Block width estimation: 5 weeks?
            weeks_in_month = 5 # approx
            bw = weeks_in_month * (cell_size + cell_gap)
            
            bx = start_x + i * (bw + gap_x)
            
            painter.drawText(bx, start_y - 4, month_str)
            
            # Draw Data
            first_day_wd = current_m.weekday() 
            iter_date = current_m
            
            while iter_date.month == current_m.month:
                day_idx = iter_date.day - 1
                rel_day = (day_idx + first_day_wd)
                col = rel_day // 7 
                row = rel_day % 7
                
                dx = bx + col * (cell_size + cell_gap)
                dy = start_y + row * (cell_size + cell_gap)
                
                d_str = iter_date.strftime("%Y-%m-%d")
                secs = self.daily_stats.get(d_str, 0)
                hours = secs / 3600
                
                painter.setBrush(QBrush(base_color))
                if hours > 0:
                    ratio = hours / self.target
                    if ratio >= 2.0: painter.setBrush(QBrush(c4))
                    elif ratio >= 1.0: painter.setBrush(QBrush(c3))
                    elif ratio >= 0.5: painter.setBrush(QBrush(c2))
                    else: painter.setBrush(QBrush(c1))
                else: 
                     painter.setBrush(QBrush(base_color))
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(dx, dy, cell_size, cell_size, 2, 2)
                
                iter_date += timedelta(days=1)
            
            # Next Month
            if current_m.month == 12:
                current_m = current_m.replace(year=current_m.year+1, month=1)
            else:
                current_m = current_m.replace(month=current_m.month+1)


from views.widgets.ela_date_picker import ElaDatePicker

# ...

class StatsPanel(DashboardCard):
    start_date_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__("数据总览", "📊", parent)
        
        # Grid Layout for boxes
        self.grid = QGridLayout()
        self.grid.setSpacing(15)
        self.content_layout.addLayout(self.grid)
        
        self.stat_widgets = {} 
        
        # 1. Start Date (0,0) - (0,1)
        self.start_date_cont = self.create_box("🚩 开始日期")
        self.date_edit = ElaDatePicker()
        self.date_edit.dateChanged.connect(self.on_date_changed)
        self.start_date_cont.layout().addWidget(self.date_edit)
        self.grid.addWidget(self.start_date_cont, 0, 0)
        
        # ... (Rest of init unchanged)
        
        # 2. Finish Date (0,1)
        self.finish_cont = self.create_box("🏁 预计完成", "--", "")
        self.stat_widgets["finish"] = self.finish_cont.findChild(QLabel, "val")
        self.grid.addWidget(self.finish_cont, 0, 1)

        # 3. Progress (0,2)
        self.progress_cont = self.create_box("📚 视频进度", "--/--", "个")
        self.stat_widgets["progress"] = self.progress_cont.findChild(QLabel, "val")
        self.grid.addWidget(self.progress_cont, 0, 2)
        
        # Row 2
        # 4. Duration (1,0)
        self.duration_cont = self.create_box("⏱ 总时长", "--", "小时")
        self.stat_widgets["duration"] = self.duration_cont.findChild(QLabel, "val")
        self.grid.addWidget(self.duration_cont, 1, 0)
        
        # 5. Today (1,1)
        self.today_cont = self.create_box("📅 今日概览", "--", "小时")
        self.stat_widgets["today"] = self.today_cont.findChild(QLabel, "val")
        self.grid.addWidget(self.today_cont, 1, 1)
        
        # 6. Balance (1,2)
        self.bal_cont = self.create_box("⚖ 学习余额", "+0.0", "小时")
        self.stat_widgets["balance"] = self.bal_cont.findChild(QLabel, "val")
        self.grid.addWidget(self.bal_cont, 1, 2)
        
        theme_manager.theme_changed.connect(self.update_style)

    def create_box(self, title, val_text=None, unit_text=None):
        f = QFrame()
        f.setObjectName("StatBox") 
        l = QVBoxLayout(f)
        l.setContentsMargins(15, 12, 15, 12)
        l.setSpacing(4)
        
        t = QLabel(title)
        t.setObjectName("title")
        l.addWidget(t)
        
        if val_text is not None:
            v = QLabel(val_text)
            v.setObjectName("val")
            l.addWidget(v)
            
        if unit_text:
            u = QLabel(unit_text)
            u.setObjectName("unit")
            l.addWidget(u)
            
        # Make it expand
        f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        return f

    def update_style(self, theme):
        # Specific styling for StatBoxes if needed, DashboardCard handles main bg
        box_style = f"""
            QFrame#StatBox {{
                background-color: {theme['bg_ter']};
                border-radius: 8px;
            }}
            QLabel#title {{ color: {theme['text_sec']}; font-size: 12px; }}
            QLabel#val {{ color: {theme['text_main']}; font-size: 18px; font-weight: bold; font-family: 'Segoe UI'; }}
            QLabel#unit {{ color: {theme['text_sec']}; font-size: 10px; }}
        """
        for w in self.findChildren(QFrame, "StatBox"):
            w.setStyleSheet(box_style)
            
        # ElaDatePicker handles its own style via ElaTheme, no need for manual QDateEdit stylesheet here.

    def on_date_changed(self, qdate):
        self.start_date_changed.emit(qdate.toString(Qt.DateFormat.ISODate))

    def update_stats(self, balance, done_v, total_v, done_h, total_h, today_h, plan_h, estimated_finish_str):
        self.stat_widgets["progress"].setText(f"{done_v}/{total_v}")
        self.stat_widgets["duration"].setText(f"{done_h:.1f}/{total_h:.1f}")
        self.stat_widgets["today"].setText(f"{today_h:.1f}/{plan_h:.1f}")
        
        bal_str = f"+{balance:.1f}" if balance >= 0 else f"{balance:.1f}"
        self.stat_widgets["balance"].setText(bal_str)
        color = theme_manager.get_theme()['accent'] if balance >= 0 else theme_manager.get_theme()['danger']
        self.stat_widgets["balance"].setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold; font-family: 'Segoe UI';")
        
        self.stat_widgets["finish"].setText(estimated_finish_str)
    
    def set_start_date(self, iso_date):
        if iso_date:
            d = QDate.fromString(iso_date, Qt.DateFormat.ISODate)
            self.date_edit.blockSignals(True)
            self.date_edit.setDate(d)
            self.date_edit.blockSignals(False)
        else:
            self.date_edit.setDate(QDate.currentDate())


class WeeklyScheduleWidget(DashboardCard):
    schedule_changed = Signal()

    def __init__(self, parent=None):
        # Prepare header controls
        self.btn_lock_work = self.create_toggle_btn("锁定工作日")
        self.btn_lock_weekend = self.create_toggle_btn("锁定双休日")
        
        self.btn_lock_plan = QPushButton("🔒 锁定计划")
        self.btn_lock_plan.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lock_plan.setCheckable(True)
        self.btn_lock_plan.clicked.connect(self.toggle_plan_lock)
        
        theme_manager.theme_changed.connect(self.update_control_style) # Bind theme
        
        controls = [self.btn_lock_work, self.btn_lock_weekend, self.btn_lock_plan]
        
        super().__init__("学习计划表 (拖动调整)", "📅", parent, header_controls=controls)
        
        self.is_plan_locked = False
        
        # Sliders in content
        self.sliders_layout = QHBoxLayout()
        self.sliders_layout.setSpacing(10)
        self.content_layout.addLayout(self.sliders_layout)
        
        self.days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        self.slider_widgets = []
        self.current_updating = False
        
        for i, day in enumerate(self.days):
            sw = DailySlider(day)
            sw.value_changed.connect(lambda v, idx=i: self.on_day_change(idx, v))
            self.slider_widgets.append(sw)
            self.sliders_layout.addWidget(sw)
            
        # Initial style
        self.update_control_style(theme_manager.get_theme())

    def create_toggle_btn(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(26)
        return btn
        
    def update_control_style(self, theme):
        # Button Styles
        lock_btn_style = f"""
            QPushButton {{
                background-color: {theme['bg_ter']};
                color: {theme['text_sec']};
                border: 1px solid {theme['border']};
                border-radius: 13px; 
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton:checked {{
                background-color: {theme['accent']};
                color: white;
                border: 1px solid {theme['accent']};
            }}
            QPushButton:hover:!checked {{
                border: 1px solid {theme['accent']};
                color: {theme['accent']};
            }}
        """
        self.btn_lock_work.setStyleSheet(lock_btn_style)
        self.btn_lock_weekend.setStyleSheet(lock_btn_style)
        
        plan_lock_style = f"""
            QPushButton {{
                background-color: {theme['bg_ter']};
                color: {theme['text_sec']};
                border: 1px solid {theme['border']};
                border-radius: 13px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:checked {{
                background-color: {theme['danger']};
                color: white;
                border: 1px solid {theme['danger']};
            }}
            QPushButton:hover:!checked {{
                border: 1px solid {theme['danger']};
                color: {theme['danger']};
            }}
        """
        self.btn_lock_plan.setStyleSheet(plan_lock_style)

    def toggle_plan_lock(self, checked):
        self.is_plan_locked = checked
        self.btn_lock_plan.setText("🔒 已锁定" if checked else "🔓 锁定计划")
        for sw in self.slider_widgets:
            sw.set_locked(checked)
            
    def on_day_change(self, msg_idx, val):
        if self.current_updating: return
        self.current_updating = True
        
        is_workday = 0 <= msg_idx <= 4
        is_weekend = 5 <= msg_idx <= 6
        
        if is_workday and self.btn_lock_work.isChecked():
            for i in range(5):
                if i != msg_idx:
                    self.slider_widgets[i].set_value(val)
                    
        if is_weekend and self.btn_lock_weekend.isChecked():
             for i in range(5, 7):
                if i != msg_idx:
                    self.slider_widgets[i].set_value(val)
        
        self.current_updating = False
        self.schedule_changed.emit()
    
    def get_schedule(self):
        return [sw.get_value() for sw in self.slider_widgets]
        
    def set_schedule(self, schedule):
        self.current_updating = True 
        for sw, val in zip(self.slider_widgets, schedule):
            sw.set_value(val)
        self.current_updating = False


class PropertiesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dm = DataManager()
        self.course_id = None
        
        # Main Layout: Scroll Area for robustness
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0,0,0,0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        # Hide scrollbar if not needed? No, auto.
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(30, 30, 30, 30) # Generous margins
        self.layout.setSpacing(25) # Card spacing
        
        self.scroll_area.setWidget(self.container)
        outer_layout.addWidget(self.scroll_area)
        
        # Heatmap Card
        self.heatmap = CourseHeatMap()
        self.layout.addWidget(self.heatmap)
        
        # Stats Card
        self.stats = StatsPanel()
        self.stats.start_date_changed.connect(self.on_start_date_changed)
        self.layout.addWidget(self.stats)
        
        # Schedule Card
        self.schedule = WeeklyScheduleWidget()
        self.schedule.schedule_changed.connect(self.save_schedule_and_recalc)
        self.layout.addWidget(self.schedule)
        
        self.layout.addStretch()
        
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(theme_manager.get_theme())
        
    def load_course(self, course_id):
        self.course_id = course_id
        course = self.dm.get_course_by_id(course_id)
        if not course: return
        
        # Load Schedule
        sched = course.get("weekly_schedule", [0]*7)
        self.schedule.set_schedule(sched)
        
        start_date = course.get("start_date")
        self.stats.set_start_date(start_date)
        
        # Refresh Logic
        self.recalc_stats()

    def on_start_date_changed(self, new_date_iso):
        if not self.course_id: return
        course = self.dm.get_course_by_id(self.course_id)
        current_sched = course.get("weekly_schedule", [0]*7)
        self.dm.set_weekly_schedule(self.course_id, current_sched, new_date_iso)
        self.recalc_stats()

    def save_schedule_and_recalc(self):
        if not self.course_id: return
        data = self.schedule.get_schedule()
        date_iso = self.stats.date_edit.date().toString(Qt.DateFormat.ISODate)
        self.dm.set_weekly_schedule(self.course_id, data, date_iso)
        self.recalc_stats()

    def recalc_stats(self):
        course = self.dm.get_course_by_id(self.course_id)
        
        # Basic Stats
        total_v = course.get("total_videos", 0)
        done_v = sum(1 for v in course["videos"] if v.get("completed"))
        total_h = course.get("total_duration", 0) / 3600
        done_h = sum(v.get("watched_duration", 0) for v in course["videos"]) / 3600
        remaining_h = total_h - done_h
        
        today_s = self.dm.get_today_progress(self.course_id)
        today_h = today_s / 3600
        
        # Plan Stats
        bal, act_min, plan_min = self.dm.get_course_balance(self.course_id)
        
        sched = course.get("weekly_schedule", [0]*7)
        wd = datetime.now().weekday()
        plan_today_h = sched[wd]
        
        # Calculate Finish Date
        finish_date_str = "--"
        if remaining_h > 0 and sum(sched) > 0:
            sim_date = date.today()
            needed = remaining_h
            if sum(sched) > 0.1: 
                days_count = 0
                while needed > 0 and days_count < 365*5:
                    day_wd = sim_date.weekday()
                    day_plan = sched[day_wd]
                    needed -= day_plan
                    if needed > 0:
                        sim_date += timedelta(days=1)
                    days_count += 1
                finish_date_str = sim_date.strftime("%Y-%m-%d")
        elif remaining_h <= 0:
            finish_date_str = "已完成"
            
        self.stats.update_stats(bal/60, done_v, total_v, done_h, total_h, today_h, plan_today_h, finish_date_str)
        
        # Heatmap
        data = course.get("daily_stats", {})
        self.heatmap.set_data(data, plan_today_h) 

    def apply_theme(self, theme):
        self.setStyleSheet(f"background-color: {theme['bg_main']};")
        self.scroll_area.setStyleSheet("border: none;")
        self.container.setStyleSheet(f"background-color: {theme['bg_main']};")
