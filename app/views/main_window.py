from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainterPath, QRegion

from views.title_bar import TitleBar
from services.theme_service import theme_service
from views.home_view import HomeView
from views.detail_view import DetailPlayerView
from models.data_manager import DataManager

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
        self._apply_theme(theme_service.get_theme())
        self.move_to_center()
    
    def _apply_theme(self, theme):
        bg_main = theme['bg_main']
        border = theme['border']
        border_radius = '0px' if self.isMaximized() else '10px'
        shadow_margin = 0 if self.isMaximized() else 10
        
        self.setStyleSheet(f"""
            MainWindow {{ background-color: transparent; }}
            #contentWidget {{ background-color: {bg_main}; border: 1px solid {border}; border-radius: {border_radius}; }}
        """)
        self.layout().setContentsMargins(shadow_margin, shadow_margin, shadow_margin, shadow_margin)
        self._apply_shadow()
    
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
            path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
            self.setMask(QRegion(path.toFillPolygon().toPolygon()))
