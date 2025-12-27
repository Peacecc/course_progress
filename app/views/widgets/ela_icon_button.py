from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent, Property, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath

from .ela_theme import ela_theme
from .ela_def import ElaThemeType, ElaIconType

class ElaIconButton(QPushButton):
    def __init__(self, awesome: ElaIconType, pixel_size=15, fixed_width=None, fixed_height=None, parent=None):
        # Handle overload signature variability
        if isinstance(pixel_size, QWidget):
            parent = pixel_size
            pixel_size = 15
        if isinstance(fixed_width, QWidget):
            parent = fixed_width
            fixed_width = None
            fixed_height = None
            
        super().__init__(parent)
        
        self._awesome = awesome
        self._border_radius = 0
        self._hover_alpha = 0
        self._opacity = 1.0
        self._is_selected = False
        self._theme_mode = ela_theme.get_theme_mode()
        
        # Colors initialized from Theme
        self._light_hover_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicHoverAlpha)
        self._dark_hover_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicHoverAlpha)
        self._light_icon_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicText)
        self._dark_icon_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicText)
        self._light_hover_icon_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicText)
        self._dark_hover_icon_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicText)
        
        ela_theme.theme_mode_changed.connect(self._on_theme_mode_changed)
        
        font = QFont("ElaAwesome")
        font.setPixelSize(pixel_size)
        self.setFont(font)
        self.setText(chr(self._awesome.value))
        
        if fixed_width and fixed_height:
            self.setFixedSize(fixed_width, fixed_height)

    def _on_theme_mode_changed(self, mode):
        self._theme_mode = mode
        self.update()

    def set_awesome(self, awesome: ElaIconType):
        self._awesome = awesome
        self.setText(chr(awesome.value))
        self.update()

    def get_awesome(self):
        return self._awesome

    # Properties
    def get_hover_alpha(self): return self._hover_alpha
    def set_hover_alpha(self, val): 
        self._hover_alpha = val
        self.update()
    pHoverAlpha = Property(int, get_hover_alpha, set_hover_alpha)

    def get_opacity(self): return self._opacity
    def set_opacity(self, val):
        self._opacity = val
        self.update()
    pOpacity = Property(float, get_opacity, set_opacity)
    
    def set_is_selected(self, val):
        if self._is_selected != val:
            self._is_selected = val
            self.update()

    def set_light_hover_color(self, color): self._light_hover_color = color
    def set_dark_hover_color(self, color): self._dark_hover_color = color
    def set_light_icon_color(self, color): self._light_icon_color = color
    def set_dark_icon_color(self, color): self._dark_icon_color = color
    def set_light_hover_icon_color(self, color): self._light_hover_icon_color = color
    def set_dark_hover_icon_color(self, color): self._dark_hover_icon_color = color

    def event(self, event):
        if event.type() == QEvent.Enter:
            if self.isEnabled() and not self._is_selected:
                self._start_alpha_animation(0, 
                                            self._light_hover_color.alpha() if self._theme_mode == ElaThemeType.ThemeMode.Light else self._dark_hover_color.alpha())
        elif event.type() == QEvent.Leave:
            if self.isEnabled() and not self._is_selected:
                self._start_alpha_animation(self._hover_alpha, 0)
        
        return super().event(event)

    def _start_alpha_animation(self, start, end):
        self._anim = QPropertyAnimation(self, b"pHoverAlpha")
        self._anim.setDuration(175)
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start(QPropertyAnimation.DeleteWhenStopped)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.save()
        painter.setOpacity(self._opacity)
        painter.setRenderHints(QPainter.SmoothPixmapTransform | QPainter.Antialiasing | QPainter.TextAntialiasing)
        painter.setPen(Qt.NoPen)
        
        # Background
        bg_color = Qt.transparent
        if self._is_selected:
            bg_color = self._light_hover_color if self._theme_mode == ElaThemeType.ThemeMode.Light else self._dark_hover_color
        elif self.isEnabled() and self.underMouse():
             # In Enter/Leave event we animate alpha, so we rely on _hover_alpha
             # But if selected, we force full hover color?
             pass
        
        # Use animated alpha color if not selected
        if not self._is_selected:
             base_hover = self._light_hover_color if self._theme_mode == ElaThemeType.ThemeMode.Light else self._dark_hover_color
             bg_color = QColor(base_hover)
             bg_color.setAlpha(self._hover_alpha)
        
        painter.setBrush(bg_color)
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)
        
        # Icon Text
        icon_color = Qt.black
        if self.isEnabled():
            if self._theme_mode == ElaThemeType.ThemeMode.Light:
                icon_color = self._light_hover_icon_color if self.underMouse() else self._light_icon_color
            else:
                icon_color = self._dark_hover_icon_color if self.underMouse() else self._dark_icon_color
        else:
            icon_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicTextDisable)
            
        painter.setPen(icon_color)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())
        
        painter.restore()
