from PySide6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, QRect, QRectF, Signal, 
                            QTimer, QEvent, QPoint, QObject, Property)
from PySide6.QtGui import QPainter, QPainterPath, QColor, QMouseEvent
from PySide6.QtWidgets import QScrollBar, QProxyStyle, QStyle, QStyleOptionSlider, QApplication, QWidget

from .ela_theme import ela_theme
from .ela_def import ElaThemeType

class ElaScrollBarStyle(QProxyStyle):
    def __init__(self, style=None):
        super().__init__(style)
        self._is_expand = False
        self._opacity = 0.0
        self._slider_extent = 2.4
        self._scroll_bar = None
        self._theme_mode = ela_theme.get_theme_mode()
        self._slider_margin = 2.5
        self._scroll_bar_extent = 10
        
        ela_theme.theme_mode_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, mode):
        self._theme_mode = mode

    def set_scroll_bar(self, scroll_bar):
        self._scroll_bar = scroll_bar

    # --- Properties for Animation ---
    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value

    def get_slider_extent(self):
        return self._slider_extent

    def set_slider_extent(self, value):
        self._slider_extent = value
    
    pOpacity = Property(float, get_opacity, set_opacity)
    pSliderExtent = Property(float, get_slider_extent, set_slider_extent)


    def drawComplexControl(self, control, option, painter, widget=None):
        if control == QStyle.CC_ScrollBar:
            if isinstance(option, QStyleOptionSlider):
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(Qt.NoPen)
                
                scroll_bar_rect = option.rect
                
                if self._is_expand:
                    # Draw Background
                    painter.setOpacity(self._opacity)
                    painter.setPen(Qt.NoPen)
                    bg_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicBase)
                    painter.setBrush(bg_color)
                    painter.drawRoundedRect(scroll_bar_rect, 6, 6)
                    
                    # Draw Indicators (Arrows)
                    side_length = 8
                    handle_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.ScrollBarHandle)
                    painter.setBrush(handle_color)
                    
                    # (Simplified indicators for brevity, full path logic can be added if needed detailed look)
                    # For now, skipping complex arrow paths to save code size unless critical. 
                    # The C++ code draws standard triangles.
                
                painter.setOpacity(1.0)
                
                # Draw Slider Handle
                slider_rect = self.subControlRect(control, option, QStyle.SC_ScrollBarSlider, widget)
                handle_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.ScrollBarHandle)
                painter.setBrush(handle_color)
                
                slider_rect_f = QRectF(slider_rect)
                if option.orientation == Qt.Horizontal:
                    # bottom aligned
                    new_h = self._slider_extent
                    new_y = slider_rect_f.bottom() - self._slider_margin - new_h
                    slider_rect_f.setRect(slider_rect_f.x(), new_y, slider_rect_f.width(), new_h)
                else:
                    # right aligned
                    new_w = self._slider_extent
                    new_x = slider_rect_f.right() - self._slider_margin - new_w
                    slider_rect_f.setRect(new_x, slider_rect_f.y(), new_w, slider_rect_f.height())
                    
                painter.drawRoundedRect(slider_rect_f, self._slider_extent / 2.0, self._slider_extent / 2.0)
                
                painter.restore()
                return

        super().drawComplexControl(control, option, painter, widget)

    def pixelMetric(self, metric, option=None, widget=None):
        if metric == QStyle.PM_ScrollBarExtent:
            return self._scroll_bar_extent
        return super().pixelMetric(metric, option, widget)

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.SH_ScrollBar_LeftClickAbsolutePosition:
            return True
        return super().styleHint(hint, option, widget, returnData)

    def start_expand_animation(self, is_expand):
        if is_expand:
            self._is_expand = True
            
            # Opacity Anim
            self._anim_opacity = QPropertyAnimation(self, b"pOpacity")
            self._anim_opacity.valueChanged.connect(lambda: self._scroll_bar.update() if self._scroll_bar else None)
            self._anim_opacity.setDuration(250)
            self._anim_opacity.setEasingCurve(QEasingCurve.InOutSine)
            self._anim_opacity.setStartValue(self._opacity)
            self._anim_opacity.setEndValue(1.0)
            self._anim_opacity.start(QPropertyAnimation.DeleteWhenStopped)
            
            # Extent Anim
            self._anim_extent = QPropertyAnimation(self, b"pSliderExtent")
            self._anim_extent.setDuration(250)
            self._anim_extent.setEasingCurve(QEasingCurve.InOutSine)
            self._anim_extent.setStartValue(self._slider_extent)
            self._anim_extent.setEndValue(self._scroll_bar_extent - 2 * self._slider_margin)
            self._anim_extent.start(QPropertyAnimation.DeleteWhenStopped)
            
        else:
            # Opacity Anim
            self._anim_opacity = QPropertyAnimation(self, b"pOpacity")
            self._anim_opacity.finished.connect(self._on_collapse_finished)
            self._anim_opacity.valueChanged.connect(lambda: self._scroll_bar.update() if self._scroll_bar else None)
            self._anim_opacity.setDuration(250)
            self._anim_opacity.setEasingCurve(QEasingCurve.InOutSine)
            self._anim_opacity.setStartValue(self._opacity)
            self._anim_opacity.setEndValue(0.0)
            self._anim_opacity.start(QPropertyAnimation.DeleteWhenStopped)
            
            # Extent Anim
            self._anim_extent = QPropertyAnimation(self, b"pSliderExtent")
            self._anim_extent.setDuration(250)
            self._anim_extent.setEasingCurve(QEasingCurve.InOutSine)
            self._anim_extent.setStartValue(self._slider_extent)
            self._anim_extent.setEndValue(2.4)
            self._anim_extent.start(QPropertyAnimation.DeleteWhenStopped)

    def _on_collapse_finished(self):
        self._is_expand = False


class ElaScrollBar(QScrollBar):
    rangeAnimationFinished = Signal()

    def __init__(self, parent=None, orientation=Qt.Vertical):
        # QScrollBar constructor issues with multiple args in PySide6 sometimes, handle carefully
        if isinstance(parent, Qt.Orientation): 
             # Handle signature mismatch if passed ElaScrollBar(Qt.Vertical, parent)
             orientation = parent
             parent = orientation
        
        super().__init__(parent)
        self.setOrientation(orientation)
        
        self.setSingleStep(1)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_Hover, True) # Important for enter/leave events
        
        self._is_animation = False
        self._scroll_value = 0
        self._is_expand = False
        
        self._style = ElaScrollBarStyle(self.style())
        self._style.set_scroll_bar(self)
        self.setStyle(self._style)
        
        # Smooth Scroll Animation
        self._slide_smooth_animation = QPropertyAnimation(self, b"value")
        self._slide_smooth_animation.setEasingCurve(QEasingCurve.OutSine)
        self._slide_smooth_animation.setDuration(300)
        self._slide_smooth_animation.finished.connect(self._on_smooth_anim_finished)
        
        # Expand Timer
        self._expand_timer = QTimer(self)
        self._expand_timer.timeout.connect(self._on_expand_timer_timeout)

    def _on_smooth_anim_finished(self):
        self._scroll_value = self.value()

    def _on_expand_timer_timeout(self):
        self._expand_timer.stop()
        self._is_expand = self.underMouse()
        self._style.start_expand_animation(self._is_expand)

    def enterEvent(self, event):
        self._expand_timer.stop()
        if not self._is_expand:
            self._expand_timer.start(350) # Delay before expanding
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._expand_timer.stop()
        if self._is_expand:
            self._expand_timer.start(350)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._slide_smooth_animation.stop()
        super().mousePressEvent(event)
        self._scroll_value = self.value()

    def mouseReleaseEvent(self, event):
        self._slide_smooth_animation.stop()
        super().mouseReleaseEvent(event)
        self._scroll_value = self.value()
        
    def mouseMoveEvent(self, event):
        self._slide_smooth_animation.stop()
        super().mouseMoveEvent(event)
        self._scroll_value = self.value()

    def wheelEvent(self, event):
        # Implement smooth scrolling for wheel
        # If animation is running, we might want to stop it or accumulate?
        # For simplicity, standard wheel event for now, or minimal smooth logic
        if self._slide_smooth_animation.state() == QPropertyAnimation.Stopped:
             self._scroll_value = self.value()

        delta = event.angleDelta().y()
        if delta != 0:
             # Basic smooth scroll logic could be added here
             # For now, let's stick to native behavior but capture value
             super().wheelEvent(event)
        else:
             super().wheelEvent(event)
             
    # TODO: Implement "bind_to_scroll_area" helper if needed to attach to QScrollArea easily
