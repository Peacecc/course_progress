from PySide6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, QRect, QPointF, Signal, 
                            QTimer, QEvent, QObject, Property, QSize)
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QSlider, QProxyStyle, QStyle, QStyleOptionSlider, QWidget

from .ela_theme import ela_theme
from .ela_def import ElaThemeType

class ElaSliderStyle(QProxyStyle):
    def __init__(self, style=None):
        super().__init__(style)
        self._theme_mode = ela_theme.get_theme_mode()
        self._last_state = QStyle.State_None
        self._circle_radius = 0.0
        ela_theme.theme_mode_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, mode):
        self._theme_mode = mode

    def get_circle_radius(self):
        return self._circle_radius

    def set_circle_radius(self, val):
        self._circle_radius = val
    
    # QProperty for animation
    circleRadius = Property(float, get_circle_radius, set_circle_radius)

    def drawComplexControl(self, control, option, painter, widget=None):
        if control == QStyle.CC_Slider:
            if isinstance(option, QStyleOptionSlider):
                painter.save()
                painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
                
                slider_rect = option.rect
                slider_handle_rect = self.subControlRect(control, option, QStyle.SC_SliderHandle, widget)
                # Adjust rect logic from C++: sliderHandleRect.adjust(1, 1, -1, -1);
                slider_handle_rect.adjust(1, 1, -1, -1)
                
                # Draw Chute (Track)
                painter.setPen(Qt.NoPen)
                chute_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicChute)
                painter.setBrush(chute_color)
                
                primary_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.PrimaryNormal)
                
                if option.orientation == Qt.Horizontal:
                    h8 = slider_rect.height() / 8
                    # Unfilled Track
                    bg_rect = QRect(slider_rect.x() + h8, 
                                    slider_rect.y() + slider_rect.height() * 0.375, 
                                    slider_rect.width() - slider_rect.height() / 4, 
                                    slider_rect.height() / 4)
                    painter.drawRoundedRect(bg_rect, h8, h8)
                    
                    # Filled Track
                    painter.setBrush(primary_color)
                    fill_rect = QRect(slider_rect.x() + h8, 
                                      slider_rect.y() + slider_rect.height() * 0.375, 
                                      slider_handle_rect.x(),  # Fill up to handle X
                                      slider_rect.height() / 4)
                    painter.drawRoundedRect(fill_rect, h8, h8)
                else:
                    w8 = slider_rect.width() / 8
                    # Unfilled Track
                    bg_rect = QRect(slider_rect.x() + slider_rect.width() * 0.375,
                                    slider_rect.y() + w8,
                                    slider_rect.width() / 4,
                                    slider_rect.height() - slider_rect.width() / 4)
                    painter.drawRoundedRect(bg_rect, w8, w8)
                    
                    # Filled Track
                    painter.setBrush(primary_color)
                    # Note: Vertical slider typically fills from bottom up or top down depending on inverted. 
                    # Providing standard implementation assuming top-down 0-max or matching C++ logic.
                    # C++ logic:
                    # QRect(sliderRect.x() + sliderRect.width() * 0.375, sliderHandleRect.y(), sliderRect.width() / 4, sliderRect.height() - sliderRect.width() / 8 - sliderHandleRect.y())
                    # This implies filling from Handle DOWN to Bottom? Or Handle UP?
                    # "sliderRect.height() - sliderRect.width() / 8 - sliderHandleRect.y()" is the height.
                    # QRect(x, y, w, h) -> y is handleY. h is distance to bottom.
                    # So this fills from Handle to Bottom.
                    
                    # Let's verify standard behavior. Usually fills from 0 (Bottom) to Handle.
                    # If C++ fills from Handle to Bottom, maybe it's Inverted? Or maybe I misread Rect logic.
                    # Let's stick to standard behavior visually: Filled part is the "Active" part.
                    # For a vertical slider, usually 0 is at bottom.
                    # But Qt default vertical slider 0 is at top unless inverted.
                    
                    # C++ Paint logic seems to fill from Handle Y down to bottom. 
                    
                    fill_rect_h = slider_rect.height() - slider_rect.width() / 8 - slider_handle_rect.y()
                    fill_rect = QRect(slider_rect.x() + slider_rect.width() * 0.375,
                                      slider_handle_rect.y(),
                                      slider_rect.width() / 4,
                                      fill_rect_h)
                    painter.drawRoundedRect(fill_rect, w8, w8)

                # Draw Handle
                # Outer Circle
                border_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicBorder)
                base_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicBase)
                painter.setPen(border_color)
                painter.setBrush(base_color)
                
                center = slider_handle_rect.center()
                # Correction +1 from C++
                center_pt = QPointF(center.x() + 1, center.y() + 1)
                
                handle_radius = slider_handle_rect.width() / 2
                painter.drawEllipse(center_pt, handle_radius, handle_radius)
                
                # Inner Circle (Animated)
                painter.setPen(Qt.NoPen)
                painter.setBrush(primary_color)
                
                if self._last_state == 0:
                     self._last_state = option.state

                # Default radius initialization
                if self._circle_radius == 0:
                     self._circle_radius = slider_handle_rect.width() / 3.8

                target_radius = slider_handle_rect.width() / 3.8 # Default 'rest' size

                current_state = option.state
                is_mouse_over = (current_state & QStyle.State_MouseOver)
                is_sunken = (current_state & QStyle.State_Sunken)  # Pressed
                
                anim_start = self._circle_radius
                anim_end = target_radius
                
                # Animation Logic
                if is_sunken:
                    if is_mouse_over:
                         # Pressing
                         target_radius = slider_handle_rect.width() / 4.5 # Smaller when pressed? C++ says 4.5
                else:
                    if is_mouse_over:
                         # Hover
                         target_radius = slider_handle_rect.width() / 2.8 # Larger when hover
                
                # Check if state changed significantly to trigger animation
                # C++ logic is a bit complex with flags. Simplifying:
                # If target changed from current known target?
                # We can just check if we need to animate towards a new target.
                
                # Ideally, we trigger animation only on state transition.
                # Simplification: if radius isn't close to target, animate.
                # But drawComplexControl is called frequently. We shouldn't start anim every frame.
                # C++ tracks _lastState to detect transition.
                
                should_anim = False
                
                # Re-implementing C++ state tracking roughly
                # MouseOver -> True
                if is_sunken:
                    if is_mouse_over:
                        if not (self._last_state & QStyle.State_Sunken):
                             # Transition to Sunken
                             should_anim = True
                             anim_end = slider_handle_rect.width() / 4.5
                else:
                    if is_mouse_over:
                        if not (self._last_state & QStyle.State_MouseOver):
                             # Transition to Hover
                             should_anim = True
                             anim_end = slider_handle_rect.width() / 2.8
                        if (self._last_state & QStyle.State_Sunken): # Released
                             should_anim = True
                             anim_end = slider_handle_rect.width() / 2.8
                    else:
                        # Normal
                        if (self._last_state & QStyle.State_MouseOver) or (self._last_state & QStyle.State_Sunken):
                             should_anim = True
                             anim_end = slider_handle_rect.width() / 3.8
                
                if should_anim:
                     self._start_radius_animation(self._circle_radius, anim_end, widget)
                
                self._last_state = current_state
                
                painter.drawEllipse(center_pt, self._circle_radius, self._circle_radius)
                
                painter.restore()
                # Stop base drawing
                return
        
        super().drawComplexControl(control, option, painter, widget)

    def pixelMetric(self, metric, option=None, widget=None):
        if metric == QStyle.PM_SliderLength:
            return 20
        if metric == QStyle.PM_SliderThickness:
            return 20
        return super().pixelMetric(metric, option, widget)

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.SH_Slider_AbsoluteSetButtons:
            return Qt.LeftButton
        return super().styleHint(hint, option, widget, returnData)

    def _start_radius_animation(self, start, end, widget):
        # We need to store animation reference to prevent GC, or use QPropertyAnimation parented to style?
        # QProxyStyle lifespan matches usage. 
        if hasattr(self, '_anim') and self._anim.state() == QPropertyAnimation.Running:
             self._anim.stop()
        
        self._anim = QPropertyAnimation(self, b"circleRadius")
        self._anim.setDuration(200) # Fast
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        
        # Lambda to update widget
        self._anim.valueChanged.connect(lambda val: widget.update() if widget else None)
        self._anim.start()


class ElaSlider(QSlider):
    def __init__(self, parent=None, orientation=Qt.Horizontal):
         # Handle signature mismatch logic
        if isinstance(parent, Qt.Orientation): 
             orientation = parent
             parent = None
        
        super().__init__(parent)
        self.setOrientation(orientation)
        self._style = ElaSliderStyle(self.style())
        self.setStyle(self._style)
        self.setAttribute(Qt.WA_Hover, True)
