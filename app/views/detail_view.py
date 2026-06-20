"""视频详情页 — 视频播放器 + 章节侧边栏 + 沉浸模式"""

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSplitter, QScrollArea, QFrame, QStackedWidget, QGridLayout,
)
from PySide6.QtCore import Qt, Signal, QTimer, QEvent, QPoint
from PySide6.QtMultimediaWidgets import QVideoWidget

from services.theme_service import theme_service
from services.player.player_service import VLC_AVAILABLE, VLCPlayerProxy, QtPlayerProxy
from views.widgets.video_widgets import VideoItemWidget, ChapterWidget
from views.widgets.video_controls import ModernVideoControls
from views.widgets.ela_scrollbar import ElaScrollBar
from views.properties_view import PropertiesView


class DetailPlayerView(QWidget):
    """视频播放详情页"""

    back_requested = Signal()
    progress_updated = Signal(str, str, float, bool)  # course_id, rel_path, watched_sec, completed

    def __init__(self, controller, parent=None):
        """
        Args:
            controller: MainController 实例
        """
        super().__init__(parent)
        self.controller = controller
        self.course_data = None
        self.player = None
        self.current_video = None
        self.video_widgets = {}
        self.pending_seek = -1

        # ---- 主布局 ----
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ---- 顶部导航栏 ----
        self._build_header()

        # ---- 页面堆栈 ----
        self.main_stack = QStackedWidget()
        self.main_layout.addWidget(self.main_stack)

        # Page 0: 播放器页
        self._build_player_page()

        # Page 1: 课程看板
        self.properties_view = PropertiesView(controller)
        self.main_stack.addWidget(self.properties_view)

        # ---- 定时器 ----
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update_ui)

        # Z-order 维护定时器
        self._z_order_timer = QTimer(self)
        self._z_order_timer.setInterval(500)
        self._z_order_timer.timeout.connect(self._maintain_z_order)
        self._z_order_timer.start()

        # 鼠标追踪
        self._mouse_check_timer = QTimer(self)
        self._mouse_check_timer.setInterval(200)
        self._mouse_check_timer.timeout.connect(self._check_mouse_motion)
        self._mouse_check_timer.start()
        self._last_mouse_pos = QPoint(-1, -1)

        # 几何同步
        self._sync_timer = QTimer(self)
        self._sync_timer.setInterval(50)
        self._sync_timer.timeout.connect(self._update_controls_geometry)
        self._sync_timer.start()

        # ---- 连接信号 ----
        self.player_controls.play_toggled.connect(self._toggle_play)
        self.player_controls.slider.sliderReleased.connect(self._on_slider_released)
        self.player_controls.fullscreen_toggled.connect(self._toggle_fullscreen)
        self.player_controls.volume_changed.connect(
            lambda v: self.player.set_volume(v) if self.player else None
        )
        self.player_controls.speed_changed.connect(
            lambda s: self.player.set_rate(s) if self.player else None
        )

        # ---- 主题 ----
        theme_service.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_service.get_theme())
        self._switch_view(0)

        # 安装主窗口事件过滤器
        QTimer.singleShot(500, self._install_main_window_filter)

    def _build_header(self):
        """构建顶部导航栏"""
        self.header_widget = QWidget()
        header_layout = QGridLayout(self.header_widget)
        header_layout.setContentsMargins(20, 10, 20, 10)

        self.back_btn = QPushButton(" 返回")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_requested.emit)
        self.back_btn.setFixedHeight(32)
        self.back_btn.setFixedWidth(64)
        header_layout.addWidget(self.back_btn, 0, 0, Qt.AlignmentFlag.AlignLeft)

        self.course_title = QLabel("Course Title")
        self.course_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.course_title, 0, 1, Qt.AlignmentFlag.AlignCenter)

        right_container = QWidget()
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.nav_player_btn = QPushButton("📺 沉浸学习")
        self.nav_prop_btn = QPushButton("📊 课程看板")
        for btn in [self.nav_player_btn, self.nav_prop_btn]:
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(120, 32)
            right_layout.addWidget(btn)

        self.nav_player_btn.clicked.connect(lambda: self._switch_view(0))
        self.nav_prop_btn.clicked.connect(lambda: self._switch_view(1))
        header_layout.addWidget(right_container, 0, 2, Qt.AlignmentFlag.AlignRight)

        header_layout.setColumnStretch(0, 1)
        header_layout.setColumnStretch(1, 2)
        header_layout.setColumnStretch(2, 1)
        self.main_layout.addWidget(self.header_widget)

    def _build_player_page(self):
        """构建播放器页面"""
        self.player_page = QWidget()
        page_layout = QVBoxLayout(self.player_page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        page_layout.addWidget(self.splitter)

        # 侧边栏
        self._build_sidebar()

        # 视频区域
        self._build_video_container()

        self.splitter.setSizes([300, 900])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        self.main_stack.addWidget(self.player_page)

    def _build_sidebar(self):
        """构建章节侧边栏"""
        self.sidebar_panel = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar_panel)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        self.list_scroll = QScrollArea()
        self.list_scroll.setWidgetResizable(True)
        self.list_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(0)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_scroll.setWidget(self.list_widget)
        self.list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_scroll.setVerticalScrollBar(ElaScrollBar(self.list_scroll))
        self.list_scroll.viewport().setStyleSheet("background: transparent;")
        self.list_scroll.setStyleSheet(self._scrollbar_qss())
        sidebar_layout.addWidget(self.list_scroll)

        self.sidebar_panel.setMinimumWidth(280)
        self.sidebar_panel.setMaximumWidth(400)
        self.sidebar_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.sidebar_panel.setStyleSheet("background-color: transparent; border-radius: 12px;")
        self.splitter.addWidget(self.sidebar_panel)
        self.splitter.setCollapsible(0, False)

    def _build_video_container(self):
        """构建视频播放容器"""
        self.content_panel = QWidget()
        self.content_layout = QVBoxLayout(self.content_panel)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.video_container = QWidget()
        self.video_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.video_container.setStyleSheet("background-color: black;")
        self.video_container.setMouseTracking(True)
        self.video_container.setCursor(Qt.CursorShape.ArrowCursor)
        container_layout = QVBoxLayout(self.video_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.video_surface = QFrame() if VLC_AVAILABLE else QVideoWidget()
        self.video_surface.setCursor(Qt.CursorShape.ArrowCursor)
        container_layout.addWidget(self.video_surface)

        self.player_controls = ModernVideoControls(self)
        self.content_layout.addWidget(self.video_container, 1)
        self.splitter.addWidget(self.content_panel)

    # ==================== 导航 ====================

    def _switch_view(self, index: int):
        self.main_stack.setCurrentIndex(index)
        self.nav_player_btn.setChecked(index == 0)
        self.nav_prop_btn.setChecked(index == 1)
        if index == 1:
            if self.player:
                self.player.pause()
            if self.course_data:
                self.properties_view.load_course(self.course_data["id"])
            self.player_controls.hide()
        else:
            self._update_controls_geometry()

    # ==================== 课程加载 ====================

    def load_course(self, course_data: dict):
        """加载课程数据"""
        self.course_data = course_data
        self.course_title.setText(course_data["name"])
        self._rebuild_sidebar()

        # 创建播放器
        if not self.player:
            if VLC_AVAILABLE:
                self.player = VLCPlayerProxy(int(self.video_surface.winId()))
            else:
                self.player = QtPlayerProxy(self.video_surface)

        self.properties_view.set_course_id(course_data["id"])

    def _rebuild_sidebar(self):
        """重建侧边栏视频列表"""
        for i in reversed(range(self.list_layout.count())):
            w = self.list_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        self.video_widgets = {}
        current_folder = None
        current_chapter = None

        for video in self.course_data["videos"]:
            dirs = video["rel_path"].split(os.sep)[:-1]
            folder_path = os.path.join(*dirs) if dirs else ""

            if folder_path != current_folder:
                current_folder = folder_path
                chapter_title = " / ".join(dirs) if dirs else "主目录"
                current_chapter = ChapterWidget(chapter_title)
                self.list_layout.addWidget(current_chapter)

            v_widget = VideoItemWidget(video)
            v_widget.clicked.connect(self._play_video)
            self.video_widgets[video["rel_path"]] = v_widget

            if current_chapter:
                current_chapter.add_widget(v_widget)
            else:
                self.list_layout.addWidget(v_widget)

        self.list_layout.addStretch()

    # ==================== 视频播放 ====================

    def _play_video(self, video_data: dict):
        """播放指定视频"""
        self.current_video = video_data

        # 高亮当前视频
        for path, w in self.video_widgets.items():
            w.set_selected(path == video_data["rel_path"])

        if not self.player:
            return

        abs_path = os.path.join(self.course_data["path"], video_data["rel_path"])

        # 停止旧媒体
        self.player.stop()
        if VLC_AVAILABLE and hasattr(self.player, "player"):
            self.player.player.video_set_mouse_input(False)
            self.player.player.video_set_key_input(False)

        # 延迟加载新媒体
        QTimer.singleShot(100, lambda: self._do_play(abs_path, video_data))

    def _do_play(self, abs_path: str, video_data: dict):
        """执行播放"""
        self.player_controls.update_time(0, 0)
        self.player.set_media(abs_path)

        # 断点续播
        start_ms = video_data.get("watched_duration", 0) * 1000
        self.player.play()
        if start_ms > 0 and not video_data.get("completed", False):
            self.pending_seek = int(start_ms)

        self.player_controls.set_playing(True)
        self.timer.start()
        self.player_controls.show_controls()
        self.player_controls.raise_()

    def _toggle_play(self):
        """播放/暂停切换"""
        if not self.player:
            return
        if self.player.is_playing():
            self.player.pause()
            self.player_controls.set_playing(False)
        else:
            self.player.play()
            self.player_controls.set_playing(True)

    def _on_slider_released(self):
        """进度条拖拽释放"""
        if self.player:
            self.player.set_time(self.player_controls.slider.value())

    def _toggle_fullscreen(self):
        """切换沉浸模式"""
        is_sidebar_visible = self.sidebar_panel.isVisible()
        new_visible = not is_sidebar_visible
        self.sidebar_panel.setVisible(new_visible)
        self.header_widget.setVisible(new_visible)
        self._apply_theme(theme_service.get_theme())
        QTimer.singleShot(50, self._update_controls_geometry)

    # ==================== 定时更新 ====================

    def _update_ui(self):
        """每秒更新播放器 UI"""
        if not self.player:
            return

        length = self.player.get_length()
        time = self.player.get_time()

        # 处理 pending seek
        if self.pending_seek != -1 and length > 0:
            self.player.set_time(self.pending_seek)
            self.pending_seek = -1

        self.player_controls.update_time(time, length)

        # 上报进度
        if length > 0 and self.current_video:
            watched_sec = int(time / 1000)
            completed = time > 0.9 * length
            self.current_video["watched_duration"] = watched_sec
            if completed:
                self.current_video["completed"] = True

            self.progress_updated.emit(
                self.course_data["id"],
                self.current_video["rel_path"],
                watched_sec,
                self.current_video.get("completed", False),
            )

            w = self.video_widgets.get(self.current_video["rel_path"])
            if w:
                w.update_icon()

    def _maintain_z_order(self):
        """维护控制栏的 Z-order"""
        if self.player_controls.isVisible():
            self.player_controls.raise_()

    # ==================== 控制栏几何 ====================

    def _update_controls_geometry(self):
        """同步控制栏的位置和大小"""
        if not self.isVisible() or self.main_stack.currentIndex() != 0:
            if self.player_controls.isVisible():
                self.player_controls.hide()
            return

        if not self.window() or not self.window().isVisible():
            self.player_controls.hide()
            return

        is_app_active = self.window().isActiveWindow() or self.player_controls.isActiveWindow()
        if not is_app_active:
            if self.player_controls.isVisible():
                self.player_controls.hide()
            return

        # 圆角状态
        is_maximized = self.window().isMaximized()
        is_sidebar_visible = self.sidebar_panel.isVisible()
        radius_right = 0 if is_maximized else 12
        radius_left = 0 if (is_maximized or is_sidebar_visible) else 12
        self.player_controls.set_rounding(radius_right, radius_left)

        # 全局坐标定位
        v_global_pos = self.video_container.mapToGlobal(QPoint(0, 0))
        self.player_controls.setGeometry(
            v_global_pos.x(), v_global_pos.y(),
            self.video_container.width(), self.video_container.height(),
        )

    def showEvent(self, event):
        super().showEvent(event)
        if self.window() and self.player_controls.parent() != self.window():
            self.player_controls.setParent(self.window(), self.player_controls.windowFlags())
            if self.main_stack.currentIndex() == 0:
                self.player_controls.show()
        QTimer.singleShot(0, self._update_controls_geometry)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.player_controls.hide_controls()
        self.player_controls.hide()

    # ==================== 鼠标追踪 ====================

    def _check_mouse_motion(self):
        """检测鼠标移动，控制控制栏显隐"""
        if not self.isVisible() or self.main_stack.currentIndex() != 0:
            return

        is_app_active = self.window().isActiveWindow() or self.player_controls.isActiveWindow()
        if not is_app_active:
            return

        from PySide6.QtGui import QCursor
        current_pos = QCursor.pos()
        if current_pos != self._last_mouse_pos:
            self._last_mouse_pos = current_pos
            lp = self.video_container.mapFromGlobal(current_pos)
            if self.video_container.rect().contains(lp):
                self.player_controls.show_controls()
                self.player_controls.raise_()
            else:
                self.player_controls.hide_controls()

    # ==================== 事件处理 ====================

    def _install_main_window_filter(self):
        win = self.window()
        if win:
            win.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched == self.window():
            if event.type() in [QEvent.Type.Move, QEvent.Type.Resize]:
                self._update_controls_geometry()
            elif event.type() == QEvent.Type.WindowStateChange:
                QTimer.singleShot(100, self._update_controls_geometry)
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self._toggle_play()
            event.accept()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_controls_geometry()

    # ==================== 主题 ====================

    def _apply_theme(self, theme):
        self.sidebar_panel.setStyleSheet(
            f"background-color: {theme['bg_sec']}; border-bottom-left-radius: 12px;"
        )
        self.header_widget.setStyleSheet(f"background-color: {theme['bg_sec']};")
        self.course_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {theme['text_main']};"
        )

        # 返回按钮
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme['text_sec']};
                border: 1px solid {theme['border']};
                border-radius: 16px;
                font-weight: bold;
                font-size: 13px;
                padding-bottom: 2px;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
                color: white;
                border: 1px solid {theme['accent']};
            }}
        """)

        self.splitter.setStyleSheet(
            f"QSplitter::handle {{ background-color: {theme['border']}; }}"
        )

        if hasattr(self, "list_scroll"):
            self.list_scroll.setStyleSheet(self._scrollbar_qss())

        # 沉浸模式圆角（播放器页）
        is_immersive = not self.sidebar_panel.isVisible()
        radius_left = "12px" if is_immersive else "0px"
        self.content_panel.setStyleSheet(
            f"background-color: {theme['bg_main']}; "
            f"border-bottom-right-radius: 12px; "
            f"border-bottom-left-radius: {radius_left};"
        )
        self.video_container.setStyleSheet(
            f"background-color: black; "
            f"border-bottom-right-radius: 12px; "
            f"border-bottom-left-radius: {radius_left};"
        )

        # 课程看板页底部圆角
        self.properties_view.setStyleSheet(
            f"background-color: {theme['bg_main']}; "
            f"border-bottom-left-radius: 12px; "
            f"border-bottom-right-radius: 12px;"
        )

        # 导航按钮
        nav_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {theme['text_sec']};
                border: 1px solid {theme['border']};
                border-radius: 16px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: {theme['accent']};
                color: white;
                border: none;
            }}
            QPushButton:hover:!checked {{
                background-color: {theme['bg_ter']};
            }}
        """
        self.nav_player_btn.setStyleSheet(nav_style)
        self.nav_prop_btn.setStyleSheet(nav_style)

    # ==================== 工具方法 ====================

    def _scrollbar_qss(self) -> str:
        theme = theme_service.get_theme()
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
