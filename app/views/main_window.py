from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainterPath, QRegion

import math
from views.title_bar import TitleBar
from services.theme_service import theme_service
from views.home_view import HomeView
from views.detail_view import DetailPlayerView
from models.data_manager import DataManager
from views.widgets.theme_animation_widget import ThemeAnimationWidget

class MainWindow(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("CourseFlow")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        self._border_width = 5
        main_layout = QVBoxLayout(self)
        shadow_margin = 10
        main_layout.setContentsMargins(shadow_margin, shadow_margin, shadow_margin, shadow_margin)
        main_layout.setSpacing(0)
        
        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentWidget")
        main_layout.addWidget(self.content_widget)
        
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.title_bar = TitleBar(self)
        content_layout.addWidget(self.title_bar)
        
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
        # 这里的 View 构造函数可能也需要调整
        self.home_view = HomeView()
        self.stack.addWidget(self.home_view)
        
        self.detail_view = DetailPlayerView()
        self.stack.addWidget(self.detail_view)
        
        theme_service.theme_changed.connect(self._apply_theme)
        # self._apply_theme(theme_service.get_theme()) # 初始主题在 TitleBar 中已经触发了一次 apply_theme，但 MainWindow 也需要设置一次
        self._apply_theme(theme_service.get_theme())
        self.move_to_center()
        
        self.theme_animation_widget = None
    
    def _apply_theme(self, theme):
        bg_main = theme['bg_main']
        border = theme['border']
        border_radius = '0px' if self.isMaximized() else '12px'
        shadow_margin = 0 if self.isMaximized() else 12
        
        self.setStyleSheet(f"""
            MainWindow {{ background-color: transparent; }}
            #contentWidget {{ background-color: {bg_main}; border: 1px solid {border}; border-radius: {border_radius}; }}
        """)
        self.layout().setContentsMargins(shadow_margin, shadow_margin, shadow_margin, shadow_margin)
        self._apply_shadow()

    def start_theme_animation(self, pos):
        if self.theme_animation_widget:
            return
            
        # 1. 捕捉当前窗口内容的截图 (旧状态)
        # 捕捉整个 content_widget，因为阴影边缘在 MainWindow 布局中
        pixmap = self.grab()
        old_image = pixmap.toImage()
        
        # 2. 切换主题 (触发各组件重绘为新状态)
        theme_service.toggle_theme()
        
        # 3. 创建并启动动画挂件 (叠加在窗口上方，显示旧状态并逐渐揭开新状态)
        self.theme_animation_widget = ThemeAnimationWidget(self)
        self.theme_animation_widget.setGeometry(self.rect())
        self.theme_animation_widget.old_window_background = old_image
        self.theme_animation_widget.center = pos
        
        # 计算结束半径 (覆盖整个窗口所需的最大距离)
        corners = [
            QPoint(0, 0),
            QPoint(self.width(), 0),
            QPoint(0, self.height()),
            QPoint(self.width(), self.height())
        ]
        max_dist = 0
        for corner in corners:
            dist = math.sqrt((pos.x() - corner.x())**2 + (pos.y() - corner.y())**2)
            if dist > max_dist:
                max_dist = dist
        
        self.theme_animation_widget.end_radius = max_dist
        self.theme_animation_widget.animationFinished.connect(self._on_theme_animation_finished)
        
        # 启动动画
        self.theme_animation_widget.start_animation(700)
    
    def _on_theme_animation_finished(self):
        self.theme_animation_widget = None
    
    def _apply_shadow(self):
        if self.isMaximized():
            self.content_widget.setGraphicsEffect(None)
        else:
            from PySide6.QtWidgets import QGraphicsDropShadowEffect
            from PySide6.QtGui import QColor
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 80))
            shadow.setOffset(0, 2)
            self.content_widget.setGraphicsEffect(shadow)
    
    def move_to_center(self):
        screen = self.screen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            window_geometry.moveCenter(screen_geometry.center())
            self.move(window_geometry.topLeft())
    
    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            self._apply_theme(theme_service.get_theme())
            self._update_round_corners()
        super().changeEvent(event)
    
    def nativeEvent(self, eventType, message):
        if eventType == "windows_generic_MSG" or eventType == b"windows_generic_MSG":
            try:
                import ctypes
                from ctypes.wintypes import MSG
                msg = MSG.from_address(int(message))
                if msg.message == 0x0084:
                    if self.isMaximized(): return super().nativeEvent(eventType, message)
                    x = ctypes.c_short(msg.lParam & 0xFFFF).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                    rect = self.frameGeometry()
                    border = self._border_width
                    on_left = x >= rect.left() and x < rect.left() + border
                    on_right = x > rect.right() - border and x <= rect.right()
                    on_top = y >= rect.top() and y < rect.top() + border
                    on_bottom = y > rect.bottom() - border and y <= rect.bottom()
                    
                    if (y >= rect.top() and y < rect.top() + self.title_bar.height() and
                        x > rect.left() + border and x < rect.right() - border):
                        return super().nativeEvent(eventType, message)
                    
                    if on_top and on_left: return True, 13
                    elif on_top and on_right: return True, 14
                    elif on_bottom and on_left: return True, 16
                    elif on_bottom and on_right: return True, 17
                    elif on_left: return True, 10
                    elif on_right: return True, 11
                    elif on_top: return True, 12
                    elif on_bottom: return True, 15
            except: pass
        return super().nativeEvent(eventType, message)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_round_corners()
    
    def _update_round_corners(self):
        if self.isMaximized(): self.clearMask()
        else:
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
            self.setMask(QRegion(path.toFillPolygon().toPolygon()))
