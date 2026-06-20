"""主窗口 — 无边框窗口框架，自定义标题栏 + 主题切换动画 + MVC 绑定"""

import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QPainterPath, QRegion, QColor, QCursor

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

        # 边缘拖拽缩放状态
        self._is_resizing = False
        self._resize_direction = None
        self._drag_start_pos = None
        self._window_start_geometry = None

        # ---- 布局 ----
        main_layout = QVBoxLayout(self)
        shadow_margin = 10
        main_layout.setContentsMargins(shadow_margin, shadow_margin, shadow_margin, shadow_margin)
        main_layout.setSpacing(0)

        # 内容容器
        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentWidget")
        self.content_widget.setMouseTracking(True)
        self.content_widget.installEventFilter(self)
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

        # print(f"[Resize] INIT: _border_width={self._border_width} shadow_margin={shadow_margin}")
        # print(f"[Resize] INIT: _RESIZE_CURSORS={self._RESIZE_CURSORS}")
        # print(f"[Resize] INIT: MainWindow.setMouseTracking={self.hasMouseTracking()}")
        # print(f"[Resize] INIT: content_widget.setMouseTracking={self.content_widget.hasMouseTracking()}")
        # print(f"[Resize] INIT: eventFilter installed on content_widget")

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

    def paintEvent(self, event):
        """用 alpha=1 填充主窗口，确保透明边距区能接收鼠标事件。

        不加这段，WA_TranslucentBackground + 透明 shadow_margin 会导致
        边缘区域的鼠标事件穿透到下层窗口，边缘拖拽缩放完全失效。
        alpha=1 在视觉上完全不可见。
        """
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        painter.end()
        event.accept()

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

    _last_logged_direction = None  # 避免鼠标移动日志刷屏

    def eventFilter(self, watched, event):
        """将 content_widget 的鼠标事件映射到 MainWindow 坐标系后统一处理。"""
        if watched is self.content_widget:
            etype = event.type()
            if etype == event.Type.MouseMove:
                mapped_pos = event.position().toPoint() + self.content_widget.pos()
                if self._is_resizing:
                    self._perform_resize(event.globalPosition().toPoint())
                    return True
                else:
                    direction = self._get_resize_direction(mapped_pos)
                    if direction != self._last_logged_direction:
                        self._last_logged_direction = direction
                        #print(f"[Resize] eventFilter Move: local=({event.position().toPoint().x()},{event.position().toPoint().y()}) mapped=({mapped_pos.x()},{mapped_pos.y()}) win=({self.rect().width()}x{self.rect().height()}) direction={direction}")
                    self._update_resize_cursor(direction)
            elif etype == event.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    mapped_pos = event.position().toPoint() + self.content_widget.pos()
                    direction = self._get_resize_direction(mapped_pos)
                    #print(f"[Resize] eventFilter Press: mapped=({mapped_pos.x()},{mapped_pos.y()}) win=({self.rect().width()}x{self.rect().height()}) direction={direction}")
                    if direction:
                        #print(f"[Resize] >>> START RESIZE (from eventFilter): {direction} <<<")
                        self._is_resizing = True
                        self._resize_direction = direction
                        self._drag_start_pos = event.globalPosition().toPoint()
                        self._window_start_geometry = self.geometry()
                        return True
            elif etype == event.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton and self._is_resizing:
                    #print(f"[Resize] <<< END RESIZE (from eventFilter) <<<")
                    self._is_resizing = False
                    self._resize_direction = None
                    return True
        return super().eventFilter(watched, event)

    _RESIZE_CURSORS = {
        "top-left":     Qt.CursorShape.SizeFDiagCursor,
        "bottom-right": Qt.CursorShape.SizeFDiagCursor,
        "top-right":    Qt.CursorShape.SizeBDiagCursor,
        "bottom-left":  Qt.CursorShape.SizeBDiagCursor,
        "left":         Qt.CursorShape.SizeHorCursor,
        "right":        Qt.CursorShape.SizeHorCursor,
        "top":          Qt.CursorShape.SizeVerCursor,
        "bottom":       Qt.CursorShape.SizeVerCursor,
    }

    def _get_resize_direction(self, pos: QPoint):
        """判断鼠标位置对应的调整方向。

        Returns:
            方向字符串 ("top-left", "right", ...) 或 None
        """
        if self.isMaximized():
            return None
        rect = self.rect()
        x, y = pos.x(), pos.y()
        b = self._border_width

        on_left = x <= b
        on_right = x >= rect.width() - b
        on_top = y <= b
        on_bottom = y >= rect.height() - b

        if on_top and on_left:
            return "top-left"
        elif on_top and on_right:
            return "top-right"
        elif on_bottom and on_left:
            return "bottom-left"
        elif on_bottom and on_right:
            return "bottom-right"
        elif on_left:
            return "left"
        elif on_right:
            return "right"
        elif on_top:
            return "top"
        elif on_bottom:
            return "bottom"
        return None

    _last_cursor_direction = None

    def _update_resize_cursor(self, direction):
        """根据方向更新鼠标光标"""
        if direction != self._last_cursor_direction:
            self._last_cursor_direction = direction
            cursor_name = self._RESIZE_CURSORS.get(direction, "ArrowCursor") if direction else "ArrowCursor"
            #print(f"[Resize] Cursor -> {cursor_name} (direction={direction}, in map={direction in self._RESIZE_CURSORS if direction else 'N/A'})")
        if direction and direction in self._RESIZE_CURSORS:
            self.setCursor(QCursor(self._RESIZE_CURSORS[direction]))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mousePressEvent(self, event):
        """边缘拖拽 → 手动调整窗口大小"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            direction = self._get_resize_direction(pos)
            #print(f"[Resize] MainWindow Press: pos=({pos.x()},{pos.y()}) win=({self.rect().width()}x{self.rect().height()}) direction={direction}")
            if direction:
                #print(f"[Resize] >>> START RESIZE (from MainWindow): {direction} <<<")
                self._is_resizing = True
                self._resize_direction = direction
                self._drag_start_pos = event.globalPosition().toPoint()
                self._window_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """边缘缩放（进行中）或光标更新"""
        if self._is_resizing:
            self._perform_resize(event.globalPosition().toPoint())
            event.accept()
        else:
            pos = event.position().toPoint()
            direction = self._get_resize_direction(pos)
            if direction != self._last_logged_direction:
                self._last_logged_direction = direction
                #print(f"[Resize] MainWindow Move: pos=({pos.x()},{pos.y()}) win=({self.rect().width()}x{self.rect().height()}) direction={direction}")
            self._update_resize_cursor(direction)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """结束边缘缩放"""
        if event.button() == Qt.MouseButton.LeftButton:
            #if self._is_resizing:
                #print(f"[Resize] <<< END RESIZE (from MainWindow) <<<")
            self._is_resizing = False
            self._resize_direction = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _perform_resize(self, global_pos: QPoint):
        """执行窗口大小调整，确保不小于最小尺寸"""
        if not self._is_resizing or not self._resize_direction:
            return

        delta = global_pos - self._drag_start_pos
        new_geo = self._window_start_geometry
        x, y, w, h = new_geo.x(), new_geo.y(), new_geo.width(), new_geo.height()

        if "left" in self._resize_direction:
            x = new_geo.x() + delta.x()
            w = new_geo.width() - delta.x()
        if "right" in self._resize_direction:
            w = new_geo.width() + delta.x()
        if "top" in self._resize_direction:
            y = new_geo.y() + delta.y()
            h = new_geo.height() - delta.y()
        if "bottom" in self._resize_direction:
            h = new_geo.height() + delta.y()

        # 确保不小于最小尺寸
        min_w = self.minimumWidth()
        min_h = self.minimumHeight()
        if w < min_w:
            if "left" in self._resize_direction:
                x = new_geo.x() + new_geo.width() - min_w
            w = min_w
        if h < min_h:
            if "top" in self._resize_direction:
                y = new_geo.y() + new_geo.height() - min_h
            h = min_h

        self.setGeometry(x, y, w, h)
