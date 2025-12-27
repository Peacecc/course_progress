from PySide6.QtWidgets import QCalendarWidget, QWidget, QVBoxLayout, QToolButton, QTableView, QSpinBox
from PySide6.QtCore import Qt, QDate, Property, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QTextCharFormat

from .ela_theme import ela_theme
from .ela_def import ElaThemeType, ElaIconType

class ElaCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(305, 340)
        
        self._border_radius = 5
        self._theme_mode = ela_theme.get_theme_mode()
        ela_theme.theme_mode_changed.connect(self._on_theme_changed)
        
        # Customize Navigation Bar
        self.setNavigationBarVisible(True)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        # self.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames) # Default
        
        # Style
        self._update_style()

    def _on_theme_changed(self, mode):
        self._theme_mode = mode
        self._update_style()

    def _update_style(self):
        # We can use qss or QPalette, or QCalendarWidget methods
        # For a truly custom look like Ela, we'd need to subclass paintCell or use QTableView delegate.
        # Here we use QSS for simplicity and "good enough" integration.
        
        bg_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.DialogBase).name()
        text_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicText).name()
        border_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicBorder).name()
        btn_hover = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicHover).name()
        primary = ela_theme.get_theme_color(ElaThemeType.ThemeColor.PrimaryNormal).name()
        
        # Navigation Bar Background
        nav_bg = ela_theme.get_theme_color(ElaThemeType.ThemeColor.WindowBase).name()

        qss = f"""
        QCalendarWidget QWidget {{
            background-color: {bg_color};
            alternate-background-color: {bg_color};
            color: {text_color};
            border: none;
        }}
        
        /* Navigation Bar */
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: {nav_bg};
            border-bottom: 1px solid {border_color};
            min-height: 40px;
        }}
        
        QCalendarWidget QToolButton {{
            color: {text_color};
            background-color: transparent;
            border-radius: 6px;
            icon-size: 16px;
            margin: 2px;
            padding: 4px;
        }}
        QCalendarWidget QToolButton:hover {{
            background-color: {btn_hover};
        }}
        QCalendarWidget QToolButton:pressed {{
            background-color: {border_color}; 
        }}
        
        /* Year/Month SpinButtons */
        QCalendarWidget QSpinBox {{
            color: {text_color};
            background-color: transparent; /* {btn_hover} */
            selection-background-color: {primary};
            selection-color: white;
            border-radius: 6px;
            padding: 2px;
            margin: 0px 4px;
            min-width: 60px;
        }}
        QCalendarWidget QSpinBox:hover {{
            background-color: {btn_hover};
        }}
        QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button {{
            subcontrol-origin: border;
            width: 0px; 
            height: 0px; 
            border: none; /* Hide native arrows for cleaner look */
        }}
        
        /* Calendar View */
        QCalendarWidget QTableView {{
            background-color: transparent;
            selection-background-color: {primary};
            selection-color: white;
            outline: 0;
            border: none;
            margin-top: 10px;
        }}
        
        QCalendarWidget QTableView::item {{
            margin: 2px;
            border-radius: 4px;
        }}
        
        QCalendarWidget QTableView::item:hover {{
            background-color: {btn_hover};
        }}
        
        QCalendarWidget QTableView::item:selected {{
            background-color: {primary};
            color: white;
        }}
        """
        self.setStyleSheet(qss)
        
    def paintCell(self, painter, rect, date):
        # Custom cell painting if needed to match Ela style perfectly
        # For now default is fine, maybe draw a round selection circle?
        if date == self.selectedDate():
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(ela_theme.get_theme_color(ElaThemeType.ThemeColor.PrimaryNormal))
            painter.drawRoundedRect(rect.adjusted(2,2,-2,-2), 4, 4)
            painter.setPen(Qt.white)
            painter.drawText(rect, Qt.AlignCenter, str(date.day()))
            painter.restore()
        else:
            super().paintCell(painter, rect, date)

    def get_selected_date(self):
        return self.selectedDate()

    def set_selected_date(self, date):
        self.setSelectedDate(date)

