from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, QFrame)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor
from services.theme_service import theme_service

class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(45)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 10, 0)
        self.layout.setSpacing(8)

        self.title_label = QLabel("CourseFlow")
        self.title_label.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.layout.addWidget(self.title_label)
        self.layout.addStretch()
        
        self.btn_theme = QPushButton()
        self.btn_theme.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_theme.setFixedSize(32, 32)
        self.btn_theme.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_theme.clicked.connect(self._on_theme_clicked)
        self.layout.addWidget(self.btn_theme)
        
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.VLine)
        self.divider.setFixedSize(1, 20)
        self.layout.addWidget(self.divider)

        self.controls_layout = QHBoxLayout()
        self.controls_layout.setSpacing(4)
        
        self.btn_min = self.create_nav_btn("─", self.minimize_window, "最小化")
        self.btn_max = self.create_nav_btn("☐", self.maximize_window, "最大化")
        self.btn_close = self.create_nav_btn("✕", self.close_window, "关闭", is_close=True)
        
        for btn in [self.btn_min, self.btn_max, self.btn_close]:
            self.controls_layout.addWidget(btn)
        self.layout.addLayout(self.controls_layout)

        self.start_pos = None
        self.normal_geometry = None
        
        theme_service.theme_changed.connect(self.apply_theme)
        self.apply_theme(theme_service.get_theme())

    def create_nav_btn(self, text, slot, tooltip, is_close=False):
        btn = QPushButton(text)
        btn.setFixedSize(32, 32)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setToolTip(tooltip)
        btn.clicked.connect(slot)
        if is_close: btn.setObjectName("btnClose")
        return btn

    def apply_theme(self, theme):
        text_main = theme['text_main']
        text_sec = theme['text_sec']
        hover_bg = theme['bg_ter']
        
        self.setStyleSheet(f"""
            TitleBar {{ background-color: transparent; border: none; }}
            QLabel {{ color: {text_main}; font-family: "Segoe UI", "Microsoft YaHei"; font-weight: bold; font-size: 15px; }}
            QPushButton {{ background-color: transparent; border: none; border-radius: 4px; color: {text_sec}; font-size: 14px; }}
            QPushButton:hover {{ background-color: {hover_bg}; color: {text_main}; }}
            QPushButton#btnClose:hover {{ background-color: {theme['danger']}; color: white; }}
        """)
        
        self.btn_theme.setText("🌙" if theme["name"] == "light" else "☀")

    def _on_theme_clicked(self):
        # 将点击位置转换为 MainWindow 的坐标
        pos = self.btn_theme.mapTo(self.window(), self.btn_theme.rect().center())
        # 触发 MainWindow 的动画
        if hasattr(self.window(), "start_theme_animation"):
            self.window().start_theme_animation(pos)
        else:
            # 回退方案
            theme_service.toggle_theme()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximize_window()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if self.start_pos:
            if self.window().isMaximized():
                ratio = event.position().x() / self.width()
                self.maximize_window(restore_pos=False)
                new_width = self.window().width()
                new_x = event.globalPosition().toPoint().x() - int(new_width * ratio)
                new_y = event.globalPosition().toPoint().y() - event.position().toPoint().y()
                self.window().move(new_x, new_y)
                self.start_pos = event.globalPosition().toPoint()
            else:
                delta = event.globalPosition().toPoint() - self.start_pos
                self.window().move(self.window().pos() + delta)
                self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event): self.start_pos = None
    def minimize_window(self): self.window().showMinimized()
    def close_window(self): self.window().close()

    def maximize_window(self, restore_pos=True):
        if self.window().isMaximized():
            self.window().showNormal()
            if restore_pos and self.normal_geometry:
                self.window().restoreGeometry(self.normal_geometry)
            self.normal_geometry = None
            self.btn_max.setText("☐")
        else:
            self.normal_geometry = self.window().saveGeometry()
            self.window().showMaximized()
            self.btn_max.setText("❐")
