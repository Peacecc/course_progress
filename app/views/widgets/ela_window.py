from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPalette

from .ela_theme import ela_theme
from .ela_def import ElaThemeType
from .ela_app_bar import ElaAppBar

class ElaWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Enable mouse tracking for cursor updates
        self.setMouseTracking(True)
        
        # Resize tracking
        self._resize_margin = 5  # Margin for resize detection
        self._resizing = False
        self._resize_edge = Qt.Edge.BottomEdge
        self._resize_start_pos = None
        self._resize_start_geometry = None
        
        
        self._central_widget_container = QWidget()
        self._central_widget_container.setObjectName("ElaWindowContainer")
        # Enable mouse tracking on child widget
        self._central_widget_container.setMouseTracking(True)
        # Add rounded corners via stylesheet
        self._central_widget_container.setStyleSheet(
            "#ElaWindowContainer { border-radius: 10px; }"
        )
        self.setCentralWidget(self._central_widget_container)
        
        self._main_layout = QVBoxLayout(self._central_widget_container)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # AppBar
        self._app_bar = ElaAppBar(self)
        self._main_layout.addWidget(self._app_bar)
        
        # Content Area
        self._container = QWidget()
        # Enable mouse tracking on content container too
        self._container.setMouseTracking(True)
        self._main_layout.addWidget(self._container)
        
        self._theme_mode = ela_theme.get_theme_mode()
        ela_theme.theme_mode_changed.connect(self._on_theme_changed)
        self._on_theme_changed(self._theme_mode)
        
        self.resize(1020, 680)

    def _on_theme_changed(self, mode):
        self._theme_mode = mode
        # Set Background Color
        bg_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.WindowBase)
        p = self.palette()
        p.setColor(QPalette.Window, bg_color)
        self.setPalette(p)
        self._central_widget_container.setAutoFillBackground(True)
        self._central_widget_container.setPalette(p)
        # Update rounded corner stylesheet with background color
        self._central_widget_container.setStyleSheet(
            f"#ElaWindowContainer {{ background-color: {bg_color.name()}; border-radius: 10px; }}"
        )

    def setWindowTitle(self, title):
        super().setWindowTitle(title)
        self._app_bar.setWindowTitle(title)

    def setIsFixedSize(self, is_fixed):
        if is_fixed:
            self.setMinimumSize(self.size())
            self.setMaximumSize(self.size())
        else:
            self.setMinimumSize(0,0)
            self.setMaximumSize(16777215, 16777215)
            
    def setIsStayTop(self, is_stay_top):
        flags = self.windowFlags()
        if is_stay_top:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        
    def setWindowButtonFlags(self, flags):
        # Placeholder or implement meaningful flags logic
        pass
    
    def getWindowButtonFlags(self):
        return 0
        
    def setUserInfoCardVisible(self, visible):
        # Placeholder for UserInfoCard
        pass
        
    def moveToCenter(self):
        from PySide6.QtGui import QScreen, QAction
        from PySide6.QtWidgets import QApplication
        
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
        
        
    def container(self):
        return self._container
    
    def _get_resize_edge(self, pos):
        """Determine which edge(s) the cursor is near for resizing"""
        rect = self.rect()
        margin = self._resize_margin
        
        edges = Qt.Edge(0)
        
        if pos.x() <= margin:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() >= rect.width() - margin:
            edges |= Qt.Edge.RightEdge
            
        if pos.y() <= margin:
            edges |= Qt.Edge.TopEdge
        elif pos.y() >= rect.height() - margin:
            edges |= Qt.Edge.BottomEdge
            
        return edges
    
    def mousePressEvent(self, event):
        """Start resize if on edge"""
        if event.button() == Qt.LeftButton:
            edges = self._get_resize_edge(event.pos())
            if edges and not self.isMaximized():
                self._resizing = True
                self._resize_edge = edges
                self._resize_start_pos = event.globalPos()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle resize dragging and cursor updates"""
        if self._resizing:
            delta = event.globalPos() - self._resize_start_pos
            # Create a COPY of the geometry to avoid mutating the original
            new_geo = self._resize_start_geometry.__class__(self._resize_start_geometry)
            
            # Adjust geometry based on edge
            if self._resize_edge & Qt.Edge.LeftEdge:
                new_geo.setLeft(new_geo.left() + delta.x())
            if self._resize_edge & Qt.Edge.RightEdge:
                new_geo.setRight(new_geo.right() + delta.x())
            if self._resize_edge & Qt.Edge.TopEdge:
                new_geo.setTop(new_geo.top() + delta.y())
            if self._resize_edge & Qt.Edge.BottomEdge:
                new_geo.setBottom(new_geo.bottom() + delta.y())
                
            # Enforce minimum size
            if new_geo.width() >= self.minimumWidth() and new_geo.height() >= self.minimumHeight():
                self.setGeometry(new_geo)
            event.accept()
        else:
            # Update cursor based on edge proximity
            if not self.isMaximized():
                edges = self._get_resize_edge(event.pos())
                self._update_cursor(edges)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """End resize"""
        if event.button() == Qt.LeftButton and self._resizing:
            self._resizing = False
            self.setCursor(Qt.ArrowCursor)  # Reset cursor
            event.accept()
        super().mouseReleaseEvent(event)
    
    def leaveEvent(self, event):
        """Reset cursor when mouse leaves window"""
        if not self._resizing:
            self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)
    
    def _update_cursor(self, edges):
        """Update cursor shape based on resize edge"""
        # No edges - set arrow cursor
        if not edges:
            self.setCursor(Qt.ArrowCursor)
            return
        
        # Check corner combinations first
        if edges == (Qt.Edge.LeftEdge | Qt.Edge.TopEdge) or edges == (Qt.Edge.RightEdge | Qt.Edge.BottomEdge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif edges == (Qt.Edge.RightEdge | Qt.Edge.TopEdge) or edges == (Qt.Edge.LeftEdge | Qt.Edge.BottomEdge):
            self.setCursor(Qt.SizeBDiagCursor)
        # Check horizontal edges
        elif edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge):
            self.setCursor(Qt.SizeHorCursor)
        # Check vertical edges
        elif edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
