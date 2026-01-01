from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QSplitter, QScrollArea, QFrame, QSlider, QComboBox, QStackedWidget, QGridLayout)
from PySide6.QtCore import Qt, Signal, QTimer, QEvent, QPoint
from PySide6.QtMultimediaWidgets import QVideoWidget
import os
from datetime import datetime, date

from services.theme_service import theme_service
from services.player.player_service import VLC_AVAILABLE, VLCPlayerProxy, QtPlayerProxy
from views.widgets.video_widgets import VideoItemWidget, ChapterWidget
from views.widgets.video_controls import ModernVideoControls
from views.widgets.ela_scrollbar import ElaScrollBar
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
        self.list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # 禁止横向滚动
        self.list_scroll.setVerticalScrollBar(ElaScrollBar(self.list_scroll)) # 使用 SDK 风格滚动条
        self.list_scroll.viewport().setStyleSheet("background: transparent;") # 关键：视口透明，防止遮挡圆角
        self.list_scroll.setStyleSheet(self._get_scrollbar_qss())
        sidebar_layout.addWidget(self.list_scroll)
        
        self.sidebar_panel.setMinimumWidth(280)
        self.sidebar_panel.setMaximumWidth(400)
        self.sidebar_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.sidebar_panel.setStyleSheet(f"QWidget {{ background-color: transparent; border-radius: 12px; }}") 
        self.splitter.addWidget(self.sidebar_panel)
        self.splitter.setCollapsible(0, False)
        
        # Content (Player)
        self.content_panel = QWidget()
        self.content_layout = QVBoxLayout(self.content_panel)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # 核心播放容器
        self.video_container = QWidget()
        self.video_container.setStyleSheet("background-color: black;")
        self.video_container.setMouseTracking(True)
        self.video_container.setCursor(Qt.CursorShape.ArrowCursor) # 确保是箭头
        self.video_container_layout = QVBoxLayout(self.video_container)
        self.video_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_surface = QFrame() if VLC_AVAILABLE else QVideoWidget()
        self.video_surface.setCursor(Qt.CursorShape.ArrowCursor) # 确保是箭头
        self.video_container_layout.addWidget(self.video_surface)
        
        # 悬浮控制层 (作为 ToolTip，拥有最高的层叠优先级)
        self.player_controls = ModernVideoControls(self)
        
        self.content_layout.addWidget(self.video_container, 1)
        self.splitter.addWidget(self.content_panel)
        self.splitter.setSizes([300, 900])
        # 核心设置：侧边栏(0)不拉伸，视频区域(1)随窗口拉伸
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        
        self.main_stack.addWidget(self.player_page)
        self.properties_view = PropertiesView()
        self.main_stack.addWidget(self.properties_view)
        
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_ui)
        
        # 信号连接
        self.player_controls.play_toggled.connect(self.toggle_play)
        self.player_controls.slider.sliderReleased.connect(self.on_slider_released)
        self.player_controls.fullscreen_toggled.connect(self.toggle_fullscreen)
        self.player_controls.volume_changed.connect(lambda v: self.player.set_volume(v) if self.player else None)
        self.player_controls.speed_changed.connect(lambda s: self.player.set_rate(s) if self.player else None)
        
        # 强制置顶定时器 (每 500ms 检查一次)
        self.z_order_timer = QTimer(self)
        self.z_order_timer.setInterval(500)
        self.z_order_timer.timeout.connect(lambda: self.player_controls.raise_() if self.player_controls.isVisible() else None)
        self.z_order_timer.start()
        
        # 鼠标追踪逻辑 (定时器轮询)
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.setInterval(200)
        self.mouse_check_timer.timeout.connect(self.check_mouse_motion)
        self.mouse_check_timer.start()
        self.last_mouse_pos = QPoint(-1, -1)
        
        # 几何位置二次同步定时器 (处理偶尔的同步延迟)
        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(50)
        self.sync_timer.timeout.connect(self.update_controls_geometry)
        self.sync_timer.start()
        
        theme_service.theme_changed.connect(self.apply_theme)
        self.apply_theme(theme_service.get_theme())
        self.switch_view(0)
        
        # 为主窗口安装事件过滤器以同步位移
        QTimer.singleShot(500, self._install_main_window_filter)

    def _install_main_window_filter(self):
        win = self.window()
        if win:
            win.installEventFilter(self)

    def showEvent(self, event):
        super().showEvent(event)
        # 视窗切换或显示时同步坐标
        # 关键：确保悬浮控制器的父对象是真正的顶级窗口，以实现桌面隔离
        if self.window() and self.player_controls.parent() != self.window():
            self.player_controls.setParent(self.window(), self.player_controls.windowFlags())
            # setParent 会改变窗口可见性，需要重新显示
            if self.main_stack.currentIndex() == 0:
                self.player_controls.show()
        
        QTimer.singleShot(0, self.update_controls_geometry)

    def _get_scrollbar_qss(self):
        theme = theme_service.get_theme()
        # 这里的 qss 会影响 ElaScrollBar 的背景和尺寸，即使它有自定义 Painter
        return f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['text_sec']}60;
                min-height: 20px;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme['accent']}cc;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """

    def hideEvent(self, event):
        super().hideEvent(event)
        # 彻底隐藏顶层悬浮窗，清理定时器
        if hasattr(self, 'player_controls'):
            self.player_controls.hide_controls()
            self.player_controls.hide()

    def update_controls_geometry(self):
        # 核心修复：如果主窗口不可见、非当前详情页、或者主窗口失去了焦点（被其他软件覆盖）
        # 则强制隐藏悬浮控制栏，防止 ToolTip 覆盖在其他软件之上
        # 注意：控制栏本身（ToolTip窗口）处于活动状态时，主窗口不是 activeWindow，
        # 所以需要额外检查控制栏是否处于活动状态
        if not self.isVisible() or self.main_stack.currentIndex() != 0 or \
           not self.window().isVisible():
            if hasattr(self, 'player_controls') and self.player_controls.isVisible():
                self.player_controls.hide()
            return
        
        # 检查窗口活动状态：主窗口或控制栏窗口任一活动即可
        is_app_active = self.window().isActiveWindow() or self.player_controls.isActiveWindow()
        if not is_app_active:
            if hasattr(self, 'player_controls') and self.player_controls.isVisible():
                self.player_controls.hide()
            return

        # 同步圆角状态
        is_maximized = self.window().isMaximized() or self.window().windowState() == Qt.WindowState.WindowFullScreen
        is_sidebar_visible = self.sidebar_panel.isVisible()
        # 右下角：最大化时取消圆角，否则保持12px
        radius_right = 0 if is_maximized else 12
        # 左下角：只有侧边栏隐藏（沉浸模式）且非最大化时才有圆角
        radius_left = 0 if is_maximized or is_sidebar_visible else 12
        self.player_controls.set_rounding(radius_right, radius_left)
        
        # 核心：使用全局坐标定位 ToolTip 窗口
        v_global_pos = self.video_container.mapToGlobal(QPoint(0, 0))
        self.player_controls.setGeometry(
            v_global_pos.x(),
            v_global_pos.y(),
            self.video_container.width(),
            self.video_container.height()
        )

    def switch_view(self, index):
        self.main_stack.setCurrentIndex(index)
        self.nav_player_btn.setChecked(index == 0)
        self.nav_prop_btn.setChecked(index == 1)
        if index == 1:
            if self.player: self.player.pause()
            if self.course_data: self.properties_view.load_course(self.course_data["id"])
            self.player_controls.hide()
        else:
            self.update_controls_geometry()

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
        
        # 1. 彻底停掉旧媒体处理
        self.player.stop()
        # 对于 VLC，允许底层 HWND 接收鼠标事件
        if VLC_AVAILABLE and hasattr(self.player, 'player'):
            self.player.player.video_set_mouse_input(False)
            self.player.player.video_set_key_input(False)
            
        # 2. 延迟加载新媒体
        QTimer.singleShot(100, lambda: self._do_play(abs_path, video_data))

    def _do_play(self, abs_path, video_data):
        self.player_controls.update_time(0, 0)
        self.player.set_media(abs_path)
        start = video_data.get("watched_duration", 0) * 1000
        self.player.play()
        if start > 0 and not video_data.get("completed"): 
            self.pending_seek = start
        self.player_controls.set_playing(True)
        self.timer.start()
        self.player_controls.show_controls()
        self.player_controls.raise_()

    def toggle_play(self):
        if not self.player: return 
        is_playing = self.player.is_playing()
        if is_playing:
            self.player.pause()
        else:
            self.player.play()
        self.player_controls.set_playing(not is_playing)

    def on_slider_released(self):
        if self.player: 
            self.player.set_time(self.player_controls.slider.value())

    def toggle_fullscreen(self):
        is_sidebar_visible = self.sidebar_panel.isVisible()
        self.sidebar_panel.setVisible(not is_sidebar_visible)
        self.header_widget.setVisible(not is_sidebar_visible)
        # 全屏切换后立即重算坐标
        QTimer.singleShot(50, self.update_controls_geometry)

    def eventFilter(self, watched, event):
        # 捕获主窗口的移动和缩放
        if watched == self.window():
            if event.type() in [QEvent.Type.Move, QEvent.Type.Resize]:
                self.update_controls_geometry()
            elif event.type() == QEvent.Type.WindowStateChange:
                # 处理最大化/恢复时的坐标同步
                QTimer.singleShot(100, self.update_controls_geometry)
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.toggle_play()
            event.accept()
        else:
            super().keyPressEvent(event)

    def check_mouse_motion(self):
        if not self.isVisible() or self.main_stack.currentIndex() != 0:
            return
        
        # 关键检查：主窗口被其他软件覆盖时，不显示控制栏，避免闪现
        is_app_active = self.window().isActiveWindow() or self.player_controls.isActiveWindow()
        if not is_app_active:
            return
        
        from PySide6.QtGui import QCursor
        current_pos = QCursor.pos()
        if current_pos != self.last_mouse_pos:
            self.last_mouse_pos = current_pos
            # 转换全局坐标到视频容器坐标进行碰撞检测
            lp = self.video_container.mapFromGlobal(current_pos)
            if self.video_container.rect().contains(lp):
                self.player_controls.show_controls()
                # 即使没动，也要确保在顶层
                self.player_controls.raise_()
            else:
                self.player_controls.hide_controls()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_controls_geometry()

    def update_ui(self):
        if not self.player: return
        length = self.player.get_length()
        time = self.player.get_time()
        if self.pending_seek != -1 and length > 0:
            self.player.set_time(self.pending_seek)
            self.pending_seek = -1
        
        self.player_controls.update_time(time, length)
        
        if length > 0 and self.current_video:
            watched_sec = int(time / 1000)
            completed = time > 0.9 * length
            self.current_video["watched_duration"] = watched_sec
            if completed: self.current_video["completed"] = True
            self.progress_updated.emit(self.course_data["id"], self.current_video["rel_path"], watched_sec, self.current_video.get("completed", False))
            w = self.video_widgets.get(self.current_video["rel_path"])
            if w: w.update_icon()

    def update_stats(self):
        # 此方法保留逻辑，但不再更新已被移除的控件
        pass

    @staticmethod
    def format_time(seconds):
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02}:{m:02}:{s:02}" if h > 0 else f"{m:02}:{s:02}"

    def apply_theme(self, theme):
        self.sidebar_panel.setStyleSheet(f"background-color: {theme['bg_sec']}; border-bottom-left-radius: 12px;") 
        self.header_widget.setStyleSheet(f"background-color: {theme['bg_sec']};")
        self.course_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {theme['text_main']};")
        self.back_btn.setStyleSheet(f"QPushButton {{ border: none; color: {theme['text_sec']}; font-weight: bold; font-size: 16px; }} QPushButton:hover {{ color: {theme['text_main']}; background-color: {theme['bg_ter']}; border-radius: 4px; }}")
        self.splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {theme['border']}; }}")
        if hasattr(self, 'list_scroll'):
            self.list_scroll.setStyleSheet(self._get_scrollbar_qss())
        self.content_panel.setStyleSheet(f"background-color: {theme['bg_main']}; border-bottom-right-radius: 12px;")
        
        nav_style = f"QPushButton {{ background-color: transparent; color: {theme['text_sec']}; border: 1px solid {theme['border']}; border-radius: 16px; font-weight: bold; }} QPushButton:checked {{ background-color: {theme['accent']}; color: white; border: none; }} QPushButton:hover {{ background-color: {theme['bg_ter']}; }}"
        self.nav_player_btn.setStyleSheet(nav_style)
        self.nav_prop_btn.setStyleSheet(nav_style)
