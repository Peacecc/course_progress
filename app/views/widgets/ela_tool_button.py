from PySide6.QtWidgets import QToolButton, QProxyStyle, QStyle, QStyleOptionToolButton, QWidget
from PySide6.QtCore import Qt, Property, QSize, QRect, QObject
from PySide6.QtGui import QPainter, QColor, QFont, QIcon, QAction

from .ela_theme import ela_theme
from .ela_def import ElaThemeType, ElaIconType

class ElaToolButtonStyle(QProxyStyle):
    def __init__(self, style=None):
        super().__init__(style)
        self._is_transparent = True
        self._border_radius = 4
        self._is_selected = False
        self._expand_icon_rotate = 0.0
        self._theme_mode = ela_theme.get_theme_mode()
        ela_theme.theme_mode_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, mode):
        self._theme_mode = mode

    def drawComplexControl(self, control, option, painter, widget=None):
        if control == QStyle.CC_ToolButton:
            if isinstance(option, QStyleOptionToolButton):
                painter.save()
                painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
                
                rect = option.rect
                if not self._is_transparent:
                     rect.adjust(1, 1, -1, -1)
                
                painter.setPen(Qt.NoPen if self._is_transparent else ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicBorder))
                
                # Background
                bg_color = Qt.transparent
                state = option.state
                
                if state & QStyle.State_Enabled:
                    if state & QStyle.State_Sunken: # Pressed
                        bg_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicPressAlpha if self._is_transparent else ElaThemeType.ThemeColor.BasicPress)
                    elif self._is_selected:
                        bg_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicSelectedAlpha if self._is_transparent else ElaThemeType.ThemeColor.BasicHover)
                    elif (state & QStyle.State_MouseOver) or (state & QStyle.State_On):
                        bg_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicHoverAlpha if self._is_transparent else ElaThemeType.ThemeColor.BasicHover)
                    elif not self._is_transparent:
                         bg_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicBase)

                if bg_color != Qt.transparent:
                    painter.setBrush(bg_color)
                    painter.drawRoundedRect(rect, self._border_radius, self._border_radius)
                
                # Text / Icon
                # Simplified drawing for now: rely on native or simple draw
                # C++ does custom drawing for ElaIcon strings.
                
                ela_icon_type = widget.property("ElaIconType")
                if ela_icon_type:
                    # Draw ElaIcon
                    icon_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicText)
                    if not (state & QStyle.State_Enabled):
                        icon_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicTextDisable)
                        
                    painter.setPen(icon_color)
                    
                    font = QFont("ElaAwesome")
                    # size logic from C++
                    icon_size = option.iconSize
                    font.setPixelSize(int(0.75 * min(icon_size.width(), icon_size.height())))
                    painter.setFont(font)
                    
                    # Assuming IconOnly for now as per minimal need
                    painter.drawText(rect, Qt.AlignCenter, ela_icon_type)
                else:
                    # Draw Standard Icon
                    if not option.icon.isNull():
                         mode = QIcon.Normal if (state & QStyle.State_Enabled) else QIcon.Disabled
                         mode = QIcon.On if (state & QStyle.State_Selected) else mode
                         pix = option.icon.pixmap(option.iconSize, mode)
                         # Center it
                         x = rect.center().x() - pix.width() // 2
                         y = rect.center().y() - pix.height() // 2
                         painter.drawPixmap(x, y, pix)

                painter.restore()
                return

        super().drawComplexControl(control, option, painter, widget)

class ElaToolButton(QToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(22, 22))
        self.setPopupMode(QToolButton.InstantPopup)
        self._style = ElaToolButtonStyle(self.style())
        self.setStyle(self._style)
        
    def set_ela_icon(self, icon: ElaIconType):
        self.setProperty("ElaIconType", chr(icon.value))
        self.update()
        
    def set_is_selected(self, val):
        self._style._is_selected = val
        self.update()
    
    def set_is_transparent(self, val):
        self._style._is_transparent = val
        self.update()
    
    def get_is_selected(self): return self._style._is_selected
