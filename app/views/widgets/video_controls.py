"""VideoControls — 视频播放控制条组件，包含播放/暂停、进度条、音量、速度调节"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QSlider, QFrame, QStyle, QStyleOptionSlider)
from PySide6.QtCore import Qt, Signal, QTimer, QRect, QPoint, QSize
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QMouseEvent, QPainterPath

class ModernProgressSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setFixedHeight(20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #0078D4;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #0078D4;
                width: 0px;
                height: 0px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)

    def enterEvent(self, event):
        self._hovered = True
        self.update_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update_style()
        super().leaveEvent(event)

    def update_style(self):
        height = 6 if self._hovered else 4
        handle_size = 12 if self._hovered else 0
        margin = -3 if self._hovered else 0
        
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: {height}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: {height//2}px;
            }}
            QSlider::sub-page:horizontal {{
                background: #0078D4;
                height: {height}px;
                border-radius: {height//2}px;
            }}
            QSlider::handle:horizontal {{
                background: #0078D4;
                width: {handle_size}px;
                height: {handle_size}px;
                margin: {margin}px 0;
                border-radius: 6px;
            }}
        """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Jump to click position
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            sr = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
            if self.orientation() == Qt.Orientation.Horizontal:
                new_val = self.minimum() + ((self.maximum() - self.minimum()) * (event.position().x() - sr.left()) / sr.width())
            else:
                new_val = self.minimum() + ((self.maximum() - self.minimum()) * (sr.bottom() - event.position().y()) / sr.height())
            self.setValue(int(new_val))
            event.accept()
        super().mousePressEvent(event)

class ModernVolumeSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            sr = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
            new_val = self.minimum() + ((self.maximum() - self.minimum()) * (event.position().x() - sr.left()) / sr.width())
            self.setValue(int(new_val))
            event.accept()
        super().mousePressEvent(event)

class ModernVideoControls(QWidget):
    play_toggled = Signal()
    seek_requested = Signal(int)
    speed_changed = Signal(float)
    volume_changed = Signal(int)
    fullscreen_toggled = Signal()

    def __init__(self, parent=None):
        # ToolTip 窗体类型在 Windows 上具有极高优先级，且能盖在原生 HWND 之上
        # 必须传入 parent 以确立所有权关系，防止其在其他虚拟桌面独立显示
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.ArrowCursor) # 确保主区域是箭头
        self._logic_parent = parent
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 底部渐变背景
        self.bg_frame = QFrame()
        self.bg_frame.setObjectName("controlBg")
        self.bg_frame.setCursor(Qt.CursorShape.ArrowCursor) # 背景层也是箭头
        self.bg_frame.setStyleSheet("QWidget#controlBg {border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;}")
        self.bg_layout = QVBoxLayout(self.bg_frame)
        self.bg_layout.setContentsMargins(15, 10, 15, 10)
        self.bg_layout.setSpacing(5)
        
        # 1. Progress Slider
        self.slider = ModernProgressSlider()
        self.bg_layout.addWidget(self.slider)
        
        # 2. Buttons Row
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(15)
        
        # Left controls
        self.play_btn = self._create_btn("▶", 32)
        self.buttons_layout.addWidget(self.play_btn)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white; font-size: 13px; font-weight: 500;")
        self.buttons_layout.addWidget(self.time_label)
        
        self.buttons_layout.addStretch()
        
        # Right controls
        self.volume_btn = self._create_btn("🔊", 32)
        self.volume_slider = ModernVolumeSlider()
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setStyleSheet(self._slider_qss())
        
        self.buttons_layout.addWidget(self.volume_btn)
        self.buttons_layout.addWidget(self.volume_slider)

        self.speeds = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        self.current_speed_idx = 0
        self.speed_btn = self._create_btn("1.0x", 60)
        self.buttons_layout.addWidget(self.speed_btn)
        
        self.fullscreen_btn = self._create_btn("⛶", 32)
        self.buttons_layout.addWidget(self.fullscreen_btn)
        
        self.bg_layout.addLayout(self.buttons_layout)
        
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.bg_frame)

        # Connections
        self.play_btn.clicked.connect(self.play_toggled.emit)
        self.speed_btn.clicked.connect(self._cycle_speed)
        self.volume_slider.valueChanged.connect(self.volume_changed.emit)
        self.volume_btn.clicked.connect(self._toggle_mute)
        self.fullscreen_btn.clicked.connect(self.fullscreen_toggled.emit)
        
        self.hide_timer = QTimer(self)
        self.hide_timer.setInterval(3000)
        self.hide_timer.timeout.connect(self.hide_controls)
        
        # 单击延迟判定定时器
        self.click_timer = QTimer(self)
        self.click_timer.setSingleShot(True)
        self.click_timer.setInterval(250)
        self.click_timer.timeout.connect(self.play_toggled.emit)
        
        self.setStyleSheet("QWidget{border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;}")

        self._is_visible = False
        self._rounding_radius = 12
        self._rounding_radius_left = 0  # 左下角圆角半径，默认不圆角（侧边栏可见时）
        self.hide()

    def _create_btn(self, text, width):
        btn = QPushButton(text)
        btn.setFixedWidth(width)
        btn.setFixedHeight(32)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus) # 防止获取焦点导致空格键失效
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #0078D4;
            }
        """)
        return btn

    def _slider_qss(self):
        return """
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #0078D4;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 10px;
                height: 10px;
                margin: -3px 0;
                border-radius: 5px;
            }
        """

    def _cycle_speed(self):
        self.current_speed_idx = (self.current_speed_idx + 1) % len(self.speeds)
        speed = self.speeds[self.current_speed_idx]
        self.speed_btn.setText(f"{speed}x")
        self.speed_changed.emit(speed)

    def _toggle_mute(self):
        if self.volume_slider.value() > 0:
            self._pre_mute_vol = self.volume_slider.value()
            self.volume_slider.setValue(0)
            self.volume_btn.setText("🔈")
        else:
            vol = getattr(self, '_pre_mute_vol', 100)
            self.volume_slider.setValue(vol)
            self.volume_btn.setText("🔊")

    def set_rounding(self, radius_right: int, radius_left: int = 0):
        """设置底部圆角。radius_right: 右下角圆角；radius_left: 左下角圆角（侧边栏隐藏时使用）"""
        if self._rounding_radius != radius_right or self._rounding_radius_left != radius_left:
            self._rounding_radius = radius_right
            self._rounding_radius_left = radius_left
            self.bg_frame.setStyleSheet(f"QWidget#controlBg {{border-bottom-left-radius: {radius_left}px; border-bottom-right-radius: {radius_right}px;}}")
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        # 如果点击的是窗口背景或非交互控件，启动延迟判定
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            # 只有点击按钮和进度条以外的区域才参与延迟判定
            if not isinstance(child, (QPushButton, QSlider)):
                self.click_timer.start()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        # 双击时拦截并取消单击定时器
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            if not isinstance(child, (QPushButton, QSlider)):
                if self.click_timer.isActive():
                    self.click_timer.stop()
                self.fullscreen_toggled.emit()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 核心：使用路径来实现圆角裁剪绘制
        path = QPainterPath()
        r_right = self._rounding_radius
        r_left = self._rounding_radius_left
        if r_right > 0 or r_left > 0:
            # 底部圆角，左右独立控制
            path.moveTo(0, 0)
            path.lineTo(self.width(), 0)
            # 右下角
            if r_right > 0:
                path.lineTo(self.width(), self.height() - r_right)
                path.quadTo(self.width(), self.height(), self.width() - r_right, self.height())
            else:
                path.lineTo(self.width(), self.height())
            # 左下角
            if r_left > 0:
                path.lineTo(r_left, self.height())
                path.quadTo(0, self.height(), 0, self.height() - r_left)
            else:
                path.lineTo(0, self.height())
            path.closeSubpath()
        else:
            path.addRect(self.rect())

        # 核心恢复：绘制一个几乎透明的层 (Alpha 1) 以确保整个 ToolTip 窗口能捕捉到鼠标事件
        painter.fillPath(path, QColor(0, 0, 0, 1))
        
        # Draw bottom gradient overlay
        gradient = QLinearGradient(0, self.height(), 0, self.height() - 100)
        gradient.setColorAt(0, QColor(0, 0, 0, 180))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.fillPath(path, gradient)
        super().paintEvent(event)

    def set_playing(self, is_playing):
        self.play_btn.setText("⏸" if is_playing else "▶")

    def update_time(self, current_ms, total_ms):
        curr = self._format_time(current_ms // 1000)
        total = self._format_time(total_ms // 1000)
        self.time_label.setText(f"{curr} / {total}")
        if not self.slider.isSliderDown() and total_ms > 0:
            self.slider.blockSignals(True)
            self.slider.setMaximum(total_ms)
            self.slider.setValue(current_ms)
            self.slider.blockSignals(False)

    def _format_time(self, seconds):
        if seconds < 0: seconds = 0
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02}:{m:02}:{s:02}" if h > 0 else f"{m:02}:{s:02}"

    def show_controls(self):
        if not self._is_visible:
            self.show()
            self.raise_()
            self._is_visible = True
            # 异步二次置顶保护
            QTimer.singleShot(50, self.raise_)
        self.hide_timer.start()

    def hide_controls(self):
        if self._is_visible:
            self.hide()
            self._is_visible = False
        self.hide_timer.stop()
