"""主窗口 — 无边框窗口框架，自定义标题栏 + 主题切换动画 + MVC 绑定"""

import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QPainterPath, QRegion, QColor, QCursor

from views.title_bar import TitleBar
from views.home_view import HomeView
from views.detail_view import DetailPlayerView
from services.theme_service import theme_service


class MainWindow(QWidget):
    """CourseFlow 主窗口"""

    def __init__(self, controller):
        """
        Args:
            controller: MainController 实例
        """
        super().__init__()
        self.controller = controller

        # ---- 窗口设置 ----
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("CourseFlow")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self._border_width = 8
        self.setMouseTracking(True)  # 鼠标悬停时追踪，用于边缘光标切换

        # ---- 布局 ----
        main_layout = QVBoxLayout(self)
        shadow_margin = 10
        main_layout.setContentsMargins(shadow_margin, shadow_margin, shadow_margin, shadow_margin)
        main_layout.setSpacing(0)

        # 内容容器
        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentWidget")
        main_layout.addWidget(self.content_widget)

        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 标题栏
        self.title_bar = TitleBar(self)
        content_layout.addWidget(self.title_bar)

        # 页面堆栈
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        # ---- 子视图（传入 Controller） ----
        self.home_view = HomeView(controller)
        self.stack.addWidget(self.home_view)

        self.detail_view = DetailPlayerView(controller)
        self.stack.addWidget(self.detail_view)

        # ---- 主题 ----
        theme_service.theme_changed.connect(self._apply_theme)
        self._apply_theme(theme_service.get_theme())

        # ---- 初始状态 ----
        self.move_to_center()
        self.theme_animation_widget = None

    # ==================== 主题 ====================

    def _apply_theme(self, theme):
        bg_main = theme["bg_main"]
        border = theme["border"]
        border_radius = "0px" if self.isMaximized() else "12px"
        shadow_margin = 0 if self.isMaximized() else 12

        self.setStyleSheet(f"""
            MainWindow {{ background-color: transparent; }}
            #contentWidget {{
                background-color: {bg_main};
                border: 1px solid {border};
                border-radius: {border_radius};
            }}
        """)
        self.layout().setContentsMargins(shadow_margin, shadow_margin, shadow_margin, shadow_margin)
        self._apply_shadow()

    def _apply_shadow(self):
        """应用窗口阴影"""
        if self.isMaximized():
            self.content_widget.setGraphicsEffect(None)
        else:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 80))
            shadow.setOffset(0, 2)
            self.content_widget.setGraphicsEffect(shadow)

    # ==================== 主题切换动画 ====================

    def start_theme_animation(self, pos: QPoint):
        """以指定位置为中心播放主题切换动画"""
        if self.theme_animation_widget:
            return

        from views.widgets.theme_animation_widget import ThemeAnimationWidget

        # 捕捉旧主题截图
        pixmap = self.grab()
        old_image = pixmap.toImage()

        # 切换主题
        theme_service.toggle_theme()

        # 启动动画
        self.theme_animation_widget = ThemeAnimationWidget(self)
        self.theme_animation_widget.setGeometry(self.rect())
        self.theme_animation_widget.old_window_background = old_image
        self.theme_animation_widget.center = pos

        corners = [
            QPoint(0, 0), QPoint(self.width(), 0),
            QPoint(0, self.height()), QPoint(self.width(), self.height()),
        ]
        max_dist = max(
            math.sqrt((pos.x() - c.x()) ** 2 + (pos.y() - c.y()) ** 2)
            for c in corners
        )
        self.theme_animation_widget.end_radius = max_dist
        self.theme_animation_widget.animationFinished.connect(self._on_animation_finished)
        self.theme_animation_widget.start_animation(700)

    def _on_animation_finished(self):
        self.theme_animation_widget = None

    # ==================== 窗口行为 ====================

    def move_to_center(self):
        """将窗口移动到屏幕中央"""
        screen = self.screen()
        if screen:
            screen_geom = screen.availableGeometry()
            window_geom = self.frameGeometry()
            window_geom.moveCenter(screen_geom.center())
            self.move(window_geom.topLeft())

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            self._apply_theme(theme_service.get_theme())
            self._update_round_corners()
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_round_corners()

    def _update_round_corners(self):
        """更新窗口圆角遮罩 — 仅遮罩内容控件，不遮罩主窗口（保留边缘拖拽区域）"""
        self.clearMask()  # 主窗口保持完整矩形，确保所有边缘可接收鼠标事件
        if not self.isMaximized():
            # 将圆角遮罩应用到内容控件上
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.content_widget.width(), self.content_widget.height(), 12, 12)
            self.content_widget.setMask(QRegion(path.toFillPolygon().toPolygon()))
        else:
            self.content_widget.clearMask()

    # ==================== 边缘拖拽缩放 ====================

    _CURSOR_MAP = {
        (True, False, False, False): Qt.CursorShape.SizeHorCursor,        # left
        (False, True, False, False): Qt.CursorShape.SizeHorCursor,        # right
        (False, False, True, False): Qt.CursorShape.SizeVerCursor,        # top
        (False, False, False, True): Qt.CursorShape.SizeVerCursor,        # bottom
        (True, False, True, False): Qt.CursorShape.SizeFDiagCursor,       # top-left
        (False, True, True, False): Qt.CursorShape.SizeBDiagCursor,       # top-right
        (True, False, False, True): Qt.CursorShape.SizeBDiagCursor,       # bottom-left
        (False, True, False, True): Qt.CursorShape.SizeFDiagCursor,       # bottom-right
    }

    def _hit_test_edges(self, pos: QPoint):
        """检测鼠标位置靠近哪些边缘。

        Returns:
            (on_left, on_right, on_top, on_bottom) 或 None（不在边缘区域）
        """
        if self.isMaximized():
            return None
        rect = self.rect()
        b = self._border_width
        on_left = pos.x() <= b
        on_right = pos.x() >= rect.width() - b
        on_top = pos.y() <= b
        on_bottom = pos.y() >= rect.height() - b
        if on_left or on_right or on_top or on_bottom:
            return (on_left, on_right, on_top, on_bottom)
        return None

    def _get_resize_edge(self, pos: QPoint):
        """获取 Qt.Edge 用于 startSystemResize"""
        edges = self._hit_test_edges(pos)
        if edges is None:
            return None
        on_left, on_right, on_top, on_bottom = edges
        edge = Qt.Edge(0)
        if on_left:
            edge |= Qt.Edge.LeftEdge
        if on_right:
            edge |= Qt.Edge.RightEdge
        if on_top:
            edge |= Qt.Edge.TopEdge
        if on_bottom:
            edge |= Qt.Edge.BottomEdge
        return edge

    def mouseMoveEvent(self, event):
        """在边缘附近时更新鼠标光标"""
        edges = self._hit_test_edges(event.position().toPoint())
        if edges is not None:
            self.setCursor(QCursor(self._CURSOR_MAP.get(edges, Qt.CursorShape.ArrowCursor)))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """边缘拖拽 → 启动系统级窗口缩放"""
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.position().toPoint())
            if edge is not None and edge != Qt.Edge(0) and self.windowHandle():
                self.windowHandle().startSystemResize(edge)
                return
        super().mousePressEvent(event)

    # ==================== Windows 原生化 ====================

    def nativeEvent(self, eventType, message):
        """处理 Windows 原生化消息（边框拖拽缩放）"""
        if eventType in ("windows_generic_MSG", b"windows_generic_MSG"):
            try:
                import ctypes
                from ctypes.wintypes import MSG
                msg = MSG.from_address(int(message))
                if msg.message == 0x0084:  # WM_NCHITTEST
                    if self.isMaximized():
                        return super().nativeEvent(eventType, message)

                    x = ctypes.c_short(msg.lParam & 0xFFFF).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                    rect = self.frameGeometry()
                    border = self._border_width

                    on_left = rect.left() <= x < rect.left() + border
                    on_right = rect.right() - border < x <= rect.right()
                    on_top = rect.top() <= y < rect.top() + border
                    on_bottom = rect.bottom() - border < y <= rect.bottom()

                    # 标题栏区域（允许拖拽）
                    title_bottom = rect.top() + self.title_bar.height()
                    if rect.top() <= y < title_bottom and on_left is False and on_right is False:
                        return super().nativeEvent(eventType, message)

                    # 边框区域 → 返回对应的 HT 值
                    if on_top and on_left: return True, 13      # HTTOPLEFT
                    elif on_top and on_right: return True, 14    # HTTOPRIGHT
                    elif on_bottom and on_left: return True, 16  # HTBOTTOMLEFT
                    elif on_bottom and on_right: return True, 17 # HTBOTTOMRIGHT
                    elif on_left: return True, 10                # HTLEFT
                    elif on_right: return True, 11               # HTRIGHT
                    elif on_top: return True, 12                 # HTTOP
                    elif on_bottom: return True, 15              # HTBOTTOM
            except Exception:
                pass
        return super().nativeEvent(eventType, message)
