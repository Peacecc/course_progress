from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt

class ElaThemeType:
    class ThemeMode:
        Light = 0
        Dark = 1

class ElaTheme:
    theme_mode_changed = Signal(int)
    def get_theme_mode(self): return 1

ela_theme = ElaTheme()

class ElaAcrylicUrlCard(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        self.title_label = QLabel("Title")
        self.sub_title_label = QLabel("SubTitle")
        layout.addWidget(self.title_label)
        layout.addWidget(self.sub_title_label)
        
    def set_title(self, text): self.title_label.setText(text)
    def set_sub_title(self, text): self.sub_title_label.setText(text)

class HeatMapWidget(QWidget): pass
class GoalCountdownWidget(QWidget): pass
