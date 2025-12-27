from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QPoint, Signal, QPointF
from PySide6.QtGui import QPainter, QPainterPath, QImage

class ThemeAnimationWidget(QWidget):
    animationFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._radius = 0.0
        self._end_radius = 1.0
        self._center = QPoint(0, 0)
        self._old_window_background = QImage()
        # 设置透明鼠标事件属性
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

    @Property(float)
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = value
        self.update()

    @Property(float)
    def end_radius(self):
        return self._end_radius

    @end_radius.setter
    def end_radius(self, value):
        self._end_radius = value

    @Property(QPoint)
    def center(self):
        return self._center

    @center.setter
    def center(self, value):
        self._center = value

    @Property(QImage)
    def old_window_background(self):
        return self._old_window_background

    @old_window_background.setter
    def old_window_background(self, value):
        self._old_window_background = value

    def start_animation(self, duration_ms):
        # 创建半径属性动画
        self.animation = QPropertyAnimation(self, b"radius")
        self.animation.setDuration(duration_ms)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(float(self._end_radius))
        self.animation.finished.connect(self._on_animation_finished)
        # 动画停止时自动删除
        self.animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self.show()

    def _on_animation_finished(self):
        # 发射动画完成信号
        self.animationFinished.emit()
        self.deleteLater()

    def paintEvent(self, event):
        if self._old_window_background.isNull():
            return

        painter = QPainter(self)
        # 设置抗锯齿和平滑变换
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        painter.setPen(Qt.PenStyle.NoPen)

        # 创建合成图像
        # 使用ARGB32格式以正确处理透明度
        animation_image = QImage(self._old_window_background.size(), QImage.Format.Format_ARGB32)
        animation_image.setDevicePixelRatio(self._old_window_background.devicePixelRatio())
        animation_image.fill(Qt.GlobalColor.transparent)

        img_painter = QPainter(animation_image)
        img_painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        
        # 绘制旧背景
        img_painter.drawImage(0, 0, self._old_window_background)
        
        # 设置合成模式为DestinationOut
        # 这个模式会移除目标区域，相当于在旧背景上"打洞"
        img_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
        
        # 创建剪切路径（圆形）
        dpr = self._old_window_background.devicePixelRatio()
        clip_path = QPainterPath()
        center_f = QPointF(self._center.x() * dpr, self._center.y() * dpr)
        clip_path.addEllipse(center_f, self._radius * dpr, self._radius * dpr)
        
        # 用黑色填充路径，由于合成模式是DestinationOut，黑色区域会被移除
        img_painter.fillPath(clip_path, Qt.GlobalColor.black)
        img_painter.end()

        # 绘制最终合成图像
        painter.drawImage(0, 0, animation_image)
        painter.end()