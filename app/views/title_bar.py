"""标题栏组件 — 无边框窗口的自定义标题栏，含窗口拖拽、菜单、主题切换和窗口控制"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QMenu, QDialog,
    QVBoxLayout, QDialogButtonBox,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor, QFont
from services.theme_service import theme_service
from version import get_version_string, get_version_info


class TitleBar(QWidget):
    """自定义标题栏 — 窗口拖拽、菜单、主题切换、窗口控制"""

    # 边缘检测宽度（与 MainWindow._border_width 保持一致）
    _EDGE_WIDTH = 8

    # 边缘 → 光标映射
    _CURSOR_MAP = {
        (True, False, False, False): Qt.CursorShape.SizeHorCursor,
        (False, True, False, False): Qt.CursorShape.SizeHorCursor,
        (False, False, True, False): Qt.CursorShape.SizeVerCursor,
        (False, False, False, True): Qt.CursorShape.SizeVerCursor,
        (True, False, True, False): Qt.CursorShape.SizeFDiagCursor,
        (False, True, True, False): Qt.CursorShape.SizeBDiagCursor,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(45)
        self.setMouseTracking(True)  # 追踪鼠标悬停，用于边缘光标切换
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 10, 0)
        self.layout.setSpacing(8)

        # ---- 标题 ----
        self.title_label = QLabel("CourseFlow")
        self.title_label.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.layout.addWidget(self.title_label)
        self.layout.addStretch()

        # ---- 菜单按钮 ----
        self.btn_menu = QPushButton("☰")
        self.btn_menu.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_menu.setFixedSize(32, 32)
        self.btn_menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_menu.setToolTip("菜单")
        self.btn_menu.clicked.connect(self._show_menu)
        self.layout.addWidget(self.btn_menu)

        # ---- 主题切换按钮 ----
        self.btn_theme = QPushButton()
        self.btn_theme.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_theme.setFixedSize(32, 32)
        self.btn_theme.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_theme.clicked.connect(self._on_theme_clicked)
        self.layout.addWidget(self.btn_theme)

        # ---- 分隔线 ----
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.VLine)
        self.divider.setFixedSize(1, 20)
        self.layout.addWidget(self.divider)

        # ---- 窗口控制按钮 ----
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

        # ---- 菜单 ----
        self._menu = None

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
        """应用主题到标题栏所有子控件"""
        text_main = theme['text_main']
        text_sec = theme['text_sec']
        hover_bg = theme['bg_ter']

        self.setStyleSheet(f"""
            TitleBar {{ background-color: transparent; border: none; }}
            QLabel {{ color: {text_main}; font-weight: bold; font-size: 15px; }}
            QPushButton {{ background-color: transparent; border: none; border-radius: 4px; color: {text_sec}; font-size: 14px; }}
            QPushButton:hover {{ background-color: {hover_bg}; color: {text_main}; }}
            QPushButton#btnClose:hover {{ background-color: {theme['danger']}; color: white; }}
            QMenu {{
                background-color: {theme['bg_sec']};
                border: 1px solid {theme['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                color: {text_main};
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {hover_bg};
            }}
        """)

        self.btn_theme.setText("🌙" if theme["name"] == "light" else "☀")

    # ==================== 菜单 ====================

    def _show_menu(self):
        """弹出标题栏菜单"""
        if self._menu is None:
            self._menu = QMenu(self)
            self._menu.setObjectName("titleBarMenu")

            action_version = self._menu.addAction("📋 关于软件")
            action_version.triggered.connect(self._show_version_dialog)

        # 将菜单定位在按钮下方
        pos = self.btn_menu.mapToGlobal(
            QPoint(0, self.btn_menu.height())
        )
        self._menu.popup(pos)

    def _show_version_dialog(self):
        """显示软件版本信息对话框"""
        info = get_version_info()
        dialog = QDialog(self.window())
        dialog.setWindowTitle("关于 CourseFlow")
        dialog.setFixedSize(380, 260)
        dialog.setWindowFlags(
            dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 应用名称
        name_label = QLabel(info["app_name"])
        name_font = QFont()
        name_font.setPointSize(18)
        name_font.setBold(True)
        name_label.setFont(name_font)
        layout.addWidget(name_label)

        # 版本号
        version_label = QLabel(f"版本 {info['version']}")
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        layout.addWidget(version_label)

        # 描述
        desc_label = QLabel(info["description"])
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addSpacing(8)

        # 版权
        copyright_label = QLabel(f"© 2024-2025 {info['author']}")
        layout.addWidget(copyright_label)

        # 确认按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn_box.accepted.connect(dialog.accept)
        layout.addWidget(btn_box)

        dialog.setStyleSheet(self._get_dialog_style())
        dialog.exec()

    def _get_dialog_style(self) -> str:
        """生成版本对话框样式表"""
        theme = theme_service.get_theme()
        return f"""
            QDialog {{
                background-color: {theme['bg_main']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
            }}
            QLabel {{
                color: {theme['text_main']};
                background: transparent;
                border: none;
            }}
            QPushButton {{
                background-color: {theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {theme['bg_ter']};
                color: {theme['text_main']};
            }}
        """

    def _on_theme_clicked(self):
        """主题切换按钮点击 — 触发主题切换动画"""
        pos = self.btn_theme.mapTo(self.window(), self.btn_theme.rect().center())
        if hasattr(self.window(), "start_theme_animation"):
            self.window().start_theme_animation(pos)
        else:
            theme_service.toggle_theme()

    # ==================== 窗口拖拽（边缘感知） ====================

    def _hit_edges(self, pos: QPoint):
        """检测鼠标位置是否在窗口边缘区域。

        仅在标题栏上下文中检查左、右、上边缘（标题栏位于窗口顶部）。

        Returns:
            (on_left, on_right, on_top) 元组，或 None
        """
        if self.window().isMaximized():
            return None
        w = self.width()
        b = self._EDGE_WIDTH
        on_left = pos.x() <= b
        on_right = pos.x() >= w - b
        on_top = pos.y() <= b
        if on_left or on_right or on_top:
            return (on_left, on_right, on_top)
        return None

    def _on_resize_edge(self, pos: QPoint) -> bool:
        """判断是否处于边缘缩放区域，若是则更新光标并返回 True"""
        edges = self._hit_edges(pos)
        if edges is None:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            return False
        on_left, on_right, on_top = edges
        cursor = self._CURSOR_MAP.get(
            (on_left, on_right, on_top, False),  # bottom 始终 False（标题栏在顶部）
            Qt.CursorShape.ArrowCursor,
        )
        self.setCursor(QCursor(cursor))
        return True

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 如果鼠标在缩放边缘区域，不启动拖拽（交由 nativeEvent / MainWindow 处理）
            if self._on_resize_edge(event.position().toPoint()):
                return
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            # 正在拖拽窗口
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
        else:
            # 更新边缘光标
            self._on_resize_edge(event.position().toPoint())

    def mouseReleaseEvent(self, event):
        self.start_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximize_window()
            event.accept()

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
