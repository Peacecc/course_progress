from PySide6.QtGui import QIcon, QFont, QFontDatabase, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QObject
import os

from .ela_theme import ela_theme
from .ela_def import ElaIconType

class ElaIcon(QObject):
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ElaIcon, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__()
        self._initialized = True
        
        # Load Font
        font_path = os.path.join(os.path.dirname(__file__), "font", "ElaAwesome.ttf")
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)
        else:
            print(f"Warning: ElaAwesome.ttf not found at {font_path}")

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = ElaIcon()
        return cls._instance

    def get_ela_icon(self, awesome: ElaIconType, pixel_size=25, fixed_width=None, fixed_height=None, color=None):
        if fixed_width is None:
            fixed_width = pixel_size
        if fixed_height is None:
            fixed_height = pixel_size
            
        pix = QPixmap(fixed_width, fixed_height)
        pix.fill(Qt.transparent)
        
        painter = QPainter(pix)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        
        if color:
            painter.setPen(color)
        else:
             # Default to current theme text color or black? C++ uses default or passed color.
             # If no color passed, let's use a reasonable default or let caller handle it.
             # C++ uses #1570A5 in one commented line, but mostly relies on caller or context.
             # Here we default to black if None, but usually caller sets it or painter has default black.
             pass

        font = QFont("ElaAwesome")
        font.setPixelSize(pixel_size)
        painter.setFont(font)
        
        # Draw Text
        # mapping Enum to char
        char_code = awesome.value
        painter.drawText(pix.rect(), Qt.AlignCenter, chr(char_code))
        
        painter.end()
        return QIcon(pix)

ela_icon = ElaIcon()
