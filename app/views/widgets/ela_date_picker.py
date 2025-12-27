from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QMenu, QWidgetAction, QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QDate, QSize
from PySide6.QtGui import QCursor, QAction

from .ela_calendar import ElaCalendar
from .ela_theme import ela_theme
from .ela_def import ElaThemeType

class ElaDatePicker(QWidget):
    dateChanged = Signal(QDate)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        
        self._date = QDate.currentDate()
        
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Button mimicking input
        self.btn = QPushButton(self._date.toString("yyyy-MM-dd"))
        self.btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn.clicked.connect(self._show_calendar)
        self.layout.addWidget(self.btn)
        
        # Style
        ela_theme.theme_mode_changed.connect(self._update_style)
        self._update_style(ela_theme.get_theme_mode())
        
    def _update_style(self, mode):
        theme = ela_theme
        bg = theme.get_theme_color(ElaThemeType.ThemeColor.DialogBase).name()
        text = theme.get_theme_color(ElaThemeType.ThemeColor.BasicText).name()
        border = theme.get_theme_color(ElaThemeType.ThemeColor.BasicBorder).name()
        hover = theme.get_theme_color(ElaThemeType.ThemeColor.BasicHover).name()
        
        # Input Field Style
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 5px 12px;
                text-align: left;
                font-family: 'Segoe UI', 'Microsoft YaHei';
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {hover};
                border: 1px solid {border};
            }}
            QPushButton:pressed {{
                background-color: {border};
            }}
        """)
        
    def _show_calendar(self):
        # Create Menu with Calendar
        menu = QMenu(self)
        
        # Transparent background for shadow effect to work if we add drop shadow wrapper
        # For now, just styling the specific menu items/container
        
        theme = ela_theme
        bg = theme.get_theme_color(ElaThemeType.ThemeColor.DialogBase).name()
        border = theme.get_theme_color(ElaThemeType.ThemeColor.BasicBorder).name()
        
        # QMenu style
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 5px;
            }}
        """)
        menu.setWindowFlags(menu.windowFlags() | Qt.NoDropShadowWindowHint | Qt.FramelessWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        
        cal_action = QWidgetAction(menu)
        self.cal = ElaCalendar()
        self.cal.setSelectedDate(self._date)
        
        # Forward signals
        self.cal.clicked.connect(lambda d: self._on_date_selected(d, menu))
        
        cal_action.setDefaultWidget(self.cal)
        menu.addAction(cal_action)
        
        # Show below button
        # Adjust pos to align nicely
        pos = self.mapToGlobal(self.rect().bottomLeft())
        pos.setY(pos.y() + 5) # Slight offset
        menu.exec(pos)
        
    def _on_date_selected(self, date, menu):
        self.setDate(date)
        menu.close()
        
    def setDate(self, date):
        self._date = date
        self.btn.setText(date.toString("yyyy-MM-dd"))
        self.dateChanged.emit(date)
        
    def date(self):
        return self._date
