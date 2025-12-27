from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QSplitter, QScrollArea, QFrame, QSlider, QComboBox, QStackedWidget, QGridLayout)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtMultimediaWidgets import QVideoWidget
import os
from datetime import datetime, date

from services.theme_service import theme_service
from services.player.player_service import VLC_AVAILABLE, VLCPlayerProxy, QtPlayerProxy
from views.widgets.video_widgets import VideoItemWidget, ChapterWidget
from views.properties_view import PropertiesView

class DetailPlayerView(QWidget):
    back_requested = Signal()
    progress_updated = Signal(str, str, int, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.course_data = None
        self.player = None
        self.current_video = None
        self.video_widgets = {}
        self.pending_seek = -1
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- HEADER ---
        self.header_widget = QWidget()
        self.header_layout = QGridLayout(self.header_widget)
        self.header_layout.setContentsMargins(20, 10, 20, 10)
        
        self.back_btn = QPushButton("← 返回")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_requested.emit)
        self.header_layout.addWidget(self.back_btn, 0, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.course_title = QLabel("Course Title")
        self.course_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_layout.addWidget(self.course_title, 0, 1, Qt.AlignmentFlag.AlignCenter)
        
        right_container = QWidget()
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(10)
        
        self.nav_player_btn = QPushButton("📺 沉浸学习")
        self.nav_prop_btn = QPushButton("📊 课程看板")
        for btn in [self.nav_player_btn, self.nav_prop_btn]:
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(120, 32)
            right_layout.addWidget(btn)
        
        self.nav_player_btn.clicked.connect(lambda: self.switch_view(0))
        self.nav_prop_btn.clicked.connect(lambda: self.switch_view(1))
        self.header_layout.addWidget(right_container, 0, 2, Qt.AlignmentFlag.AlignRight)
        
        self.header_layout.setColumnStretch(0, 1)
        self.header_layout.setColumnStretch(1, 2)
        self.header_layout.setColumnStretch(2, 1)
        self.main_layout.addWidget(self.header_widget)
        
        # --- STACK ---
        self.main_stack = QStackedWidget()
        self.main_layout.addWidget(self.main_stack)
        
        # Page 0: Player
        self.player_page = QWidget()
        player_page_layout = QVBoxLayout(self.player_page)
        player_page_layout.setContentsMargins(0,0,0,0)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        player_page_layout.addWidget(self.splitter)
        
        # Sidebar
        self.sidebar_panel = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar_panel)
        sidebar_layout.setContentsMargins(0,0,0,0)
        self.list_scroll = QScrollArea()
        self.list_scroll.setWidgetResizable(True)
        self.list_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(0)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setContentsMargins(0,0,0,0)
        self.list_scroll.setWidget(self.list_widget)
        sidebar_layout.addWidget(self.list_scroll)
        self.splitter.addWidget(self.sidebar_panel)
        
        # Content
        self.content_panel = QWidget()
        self.content_layout = QVBoxLayout(self.content_panel)
        self.content_layout.setContentsMargins(0,0,0,0)
        self.content_layout.setSpacing(0)
        
        self.video_container = QWidget()
        self.video_container.setStyleSheet("background-color: black;")
        self.video_container_layout = QVBoxLayout(self.video_container)
        self.video_container_layout.setContentsMargins(0,0,0,0)
        self.video_surface = QFrame() if VLC_AVAILABLE else QVideoWidget()
        self.video_container_layout.addWidget(self.video_surface)
        self.content_layout.addWidget(self.video_container, 1)
        
        # Controls
        self.controls_widget = QWidget()
        self.controls_widget.setFixedHeight(80)
        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.controls_layout.addWidget(self.slider)
        
        btn_row = QHBoxLayout()
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self.toggle_play)
        btn_row.addWidget(self.play_btn)
        self.time_label = QLabel("00:00 / 00:00")
        btn_row.addWidget(self.time_label)
        btn_row.addStretch()
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        btn_row.addWidget(self.speed_combo)
        self.controls_layout.addLayout(btn_row)
        self.content_layout.addWidget(self.controls_widget)
        
        # Stats
        self.stats_widget = QFrame()
        self.stats_layout = QHBoxLayout(self.stats_widget)
        self.goal_badge = QLabel("今日目标: --")
        self.stats_desc = QLabel("总进度: --")
        self.stats_layout.addWidget(self.goal_badge)
        self.stats_layout.addStretch()
        self.stats_layout.addWidget(self.stats_desc)
        self.content_layout.addWidget(self.stats_widget)
        self.splitter.addWidget(self.content_panel)
        self.splitter.setSizes([300, 900])
        
        self.main_stack.addWidget(self.player_page)
        self.properties_view = PropertiesView()
        self.main_stack.addWidget(self.properties_view)
        
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_ui)
        self.is_slider_dragging = False
        self.slider.sliderPressed.connect(lambda: setattr(self, 'is_slider_dragging', True))
        self.slider.sliderReleased.connect(self.on_slider_released)
        
        theme_service.theme_changed.connect(self.apply_theme)
        self.apply_theme(theme_service.get_theme())
        self.switch_view(0)

    def switch_view(self, index):
        self.main_stack.setCurrentIndex(index)
        self.nav_player_btn.setChecked(index == 0)
        self.nav_prop_btn.setChecked(index == 1)
        if index == 1:
            if self.player: self.player.pause()
            if self.course_data: self.properties_view.load_course(self.course_data["id"])

    def load_course(self, course_data):
        self.course_data = course_data
        self.course_title.setText(course_data["name"])
        self.rebuild_sidebar()
        self.update_stats()
        if not self.player:
            if VLC_AVAILABLE:
                self.player = VLCPlayerProxy(int(self.video_surface.winId()))
            else:
                self.player = QtPlayerProxy(self.video_surface)
        self.properties_view.course_id = course_data["id"]

    def rebuild_sidebar(self):
        for i in reversed(range(self.list_layout.count())): 
            w = self.list_layout.itemAt(i).widget()
            if w: w.setParent(None)
        self.video_widgets = {}
        current_folder = None
        current_chapter = None
        for video in self.course_data["videos"]:
            dirs = video["rel_path"].split(os.sep)[:-1]
            folder_path = os.path.join(*dirs) if dirs else ""
            if folder_path != current_folder:
                current_folder = folder_path
                current_chapter = ChapterWidget(" / ".join(dirs) if dirs else "主目录")
                self.list_layout.addWidget(current_chapter)
            v_widget = VideoItemWidget(video)
            v_widget.clicked.connect(self.play_video)
            self.video_widgets[video["rel_path"]] = v_widget
            if current_chapter: current_chapter.add_widget(v_widget)
            else: self.list_layout.addWidget(v_widget)
        self.list_layout.addStretch()

    def play_video(self, video_data):
        self.current_video = video_data
        for path, w in self.video_widgets.items():
            w.set_selected(path == video_data["rel_path"])
        abs_path = os.path.join(self.course_data["path"], video_data["rel_path"])
        if not self.player: return
        self.player.set_media(abs_path)
        start = video_data.get("watched_duration", 0) * 1000
        self.player.play()
        if start > 0 and not video_data.get("completed"): self.pending_seek = start
        self.play_btn.setText("⏸")
        self.timer.start()

    def toggle_play(self):
        if not self.player: return 
        if self.player.is_playing():
            self.player.pause()
            self.play_btn.setText("▶")
        else:
            self.player.play()
            self.play_btn.setText("⏸")

    def on_slider_released(self):
        self.is_slider_dragging = False
        if self.player: self.player.set_time(self.slider.value())

    def update_ui(self):
        if not self.player: return
        length = self.player.get_length()
        time = self.player.get_time()
        if self.pending_seek != -1 and length > 0:
            self.player.set_time(self.pending_seek)
            self.pending_seek = -1
        if not self.is_slider_dragging:
            self.slider.setMaximum(length)
            self.slider.setValue(time)
        self.time_label.setText(f"{self.format_time(time/1000)} / {self.format_time(length/1000)}")
        if length > 0 and self.current_video:
            watched_sec = int(time / 1000)
            completed = time > 0.9 * length
            self.current_video["watched_duration"] = watched_sec
            if completed: self.current_video["completed"] = True
            self.progress_updated.emit(self.course_data["id"], self.current_video["rel_path"], watched_sec, self.current_video.get("completed", False))
            w = self.video_widgets.get(self.current_video["rel_path"])
            if w: w.update_icon()
            self.update_stats()

    def update_stats(self):
        total_dur = self.course_data.get("total_duration", 0)
        watched_dur = sum(v.get("watched_duration", 0) for v in self.course_data["videos"])
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_done = self.course_data.get("daily_stats", {}).get(today_str, 0)
        self.goal_badge.setText(f"今日已学: {self.format_time(today_done)}")
        self.stats_desc.setText(f"总进度: {int(watched_dur/total_dur*100) if total_dur else 0}%")

    @staticmethod
    def format_time(seconds):
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02}:{m:02}:{s:02}" if h > 0 else f"{m:02}:{s:02}"

    def apply_theme(self, theme):
        self.sidebar_panel.setStyleSheet(f"background-color: {theme['bg_sec']}; border-bottom-left-radius: 12px;") 
        self.header_widget.setStyleSheet(f"background-color: {theme['bg_sec']}; border-top-left-radius: 12px;")
        self.course_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {theme['text_main']};")
        self.back_btn.setStyleSheet(f"QPushButton {{ border: none; color: {theme['text_sec']}; font-weight: bold; font-size: 16px; }} QPushButton:hover {{ color: {theme['text_main']}; background-color: {theme['bg_ter']}; border-radius: 4px; }}")
        self.splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {theme['border']}; }}")
        self.content_panel.setStyleSheet(f"background-color: {theme['bg_main']}; border-bottom-right-radius: 12px;")
        self.controls_widget.setStyleSheet(f"background-color: {theme['bg_sec']}; border-top: 1px solid {theme['border']};")
        self.play_btn.setStyleSheet(f"color: {theme['text_main']}; font-size: 16px; border: 1px solid {theme['text_sec']}; border-radius: 16px;")
        self.stats_widget.setStyleSheet(f"background-color: {theme['bg_sec']}; color: {theme['text_sec']}; border-top: 1px solid {theme['border']}; border-bottom-right-radius: 12px;")
        nav_style = f"QPushButton {{ background-color: transparent; color: {theme['text_sec']}; border: 1px solid {theme['border']}; border-radius: 16px; font-weight: bold; }} QPushButton:checked {{ background-color: {theme['accent']}; color: white; border: none; }} QPushButton:hover {{ background-color: {theme['bg_ter']}; }}"
        self.nav_player_btn.setStyleSheet(nav_style)
        self.nav_prop_btn.setStyleSheet(nav_style)
