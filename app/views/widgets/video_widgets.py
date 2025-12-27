from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QIcon, QCursor
from  services.theme_service import theme_service as theme_manager

class VideoItemWidget(QFrame):
    clicked = Signal(object) # video_data

    def __init__(self, video_data, parent=None):
        super().__init__(parent)
        self.video_data = video_data
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(50)
        
        self.is_selected = False
        self.is_hovered = False
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)
        
        # Icon / Status
        self.icon_label = QLabel()
        self.update_icon()
        layout.addWidget(self.icon_label)
        
        # Title
        title_str = video_data["rel_path"].split("\\")[-1].split("/")[-1]
        self.title_label = QLabel(title_str)
        layout.addWidget(self.title_label, 1)
        
        # Duration
        duration_str = self.format_time(video_data.get("duration", 0))
        self.dur_label = QLabel(duration_str)
        layout.addWidget(self.dur_label)
        
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(theme_manager.get_theme())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.video_data)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.is_hovered = True
        self.refresh_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.refresh_style()
        super().leaveEvent(event)

    def set_selected(self, selected):
        self.is_selected = selected
        self.refresh_style()

    def update_icon(self):
        if self.video_data.get("completed"):
            self.icon_label.setText("✅")
        elif self.video_data.get("watched_duration", 0) > 0:
            self.icon_label.setText("🕒")
        else:
            self.icon_label.setText("📄")

    def apply_theme(self, theme):
        self.current_theme = theme
        self.title_label.setStyleSheet(f"font-size: 13px; color: {theme['text_main']};")
        self.dur_label.setStyleSheet(f"color: {theme['text_sec']}; font-size: 12px;")
        self.refresh_style()

    def refresh_style(self):
        if not hasattr(self, 'current_theme'): return
        theme = self.current_theme
        
        bg = "transparent"
        border = "none"
        
        if self.is_selected:
            bg = theme['bg_ter']
            border = f"1px solid {theme['accent']}"
        elif self.is_hovered:
            bg = theme['bg_ter']
            
        self.setStyleSheet(f"""
            VideoItemWidget {{
                background-color: {bg};
                border: {border};
                border-radius: 4px;
            }}
        """)

    @staticmethod
    def format_time(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(m):02}:{int(s):02}"


class ChapterWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.layout.setSpacing(0)
        
        # Header Button
        self.header = QPushButton(title)
        self.header.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.header.clicked.connect(self.toggle_expanded)
        self.layout.addWidget(self.header)
        
        # Content Area
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(15, 0, 0, 0) # Indent children
        self.content_layout.setSpacing(2)
        self.layout.addWidget(self.content_area)
        
        self.is_expanded = True
        
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(theme_manager.get_theme())
        
    def add_widget(self, widget):
        self.content_layout.addWidget(widget)
        
    def toggle_expanded(self):
        self.is_expanded = not self.is_expanded
        self.content_area.setVisible(self.is_expanded)
        
    def apply_theme(self, theme):
        self.header.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                background-color: transparent;
                color: {theme['text_main']};
                font-weight: bold;
                font-size: 14px;
                padding: 8px 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {theme['bg_ter']};
                border-radius: 4px;
            }}
        """)
