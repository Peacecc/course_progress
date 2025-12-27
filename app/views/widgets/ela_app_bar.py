from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from .ela_theme import ela_theme  
from .ela_def import ElaThemeType, ElaIconType
from .ela_tool_button import ElaToolButton
from .ela_icon_button import ElaIconButton

class ElaAppBar(QWidget):
    routeBackButtonClicked = Signal()
    routeForwardButtonClicked = Signal()
    navigationButtonClicked = Signal()
    themeChangeButtonClicked = Signal()
    closeButtonClicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(45)
        self._is_stay_top = False
        
        # 设置透明背景
        self.setObjectName("ElaAppBar")
        self.setStyleSheet("#ElaAppBar{background-color:transparent;}")
        
        self._main_layout = QHBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # --- 左侧布局 ---
        left_layout = QHBoxLayout()
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setAlignment(Qt.AlignLeft)
        
        # 返回按钮
        self._route_back_button = ElaToolButton(self)
        self._route_back_button.set_ela_icon(ElaIconType.ArrowLeft)
        self._route_back_button.setFixedSize(35, 30)
        self._route_back_button.setEnabled(False)
        self._route_back_button.clicked.connect(self.routeBackButtonClicked)
        
        # 前进按钮
        self._route_forward_button = ElaToolButton(self)
        self._route_forward_button.set_ela_icon(ElaIconType.ArrowRight)
        self._route_forward_button.setFixedSize(35, 30)
        self._route_forward_button.setEnabled(False)
        self._route_forward_button.clicked.connect(self.routeForwardButtonClicked)
        
        # 导航按钮（菜单图标）
        self._navigation_button = ElaToolButton(self)
        self._navigation_button.set_ela_icon(ElaIconType.Bars)
        self._navigation_button.setFixedSize(40, 30)
        self._navigation_button.setVisible(False)  # 默认隐藏
        self._navigation_button.clicked.connect(self.navigationButtonClicked)
        
        # 图标标签
        self._icon_label = QLabel(self)
        self._icon_label_layout = self._create_vlayout(self._icon_label)
        if parent and not parent.windowIcon().isNull():
            self._icon_label.setPixmap(parent.windowIcon().pixmap(18, 18))
            self._icon_label_layout.setContentsMargins(10, 0, 0, 0)
        else:
            self._icon_label.setVisible(False)
            
        # 连接父窗口的图标改变信号
        if parent:
            parent.windowIconChanged.connect(self._on_window_icon_changed)
        
        # 标题标签
        self._title_label = QLabel(self)
        self._title_label.setObjectName("ElaAppBarTitle")
        font = self._title_label.font()
        font.setPixelSize(13)
        self._title_label.setFont(font)
        self._title_label_layout = self._create_vlayout(self._title_label)
        
        if parent and parent.windowTitle():
            self._title_label.setText(parent.windowTitle())
            self._title_label_layout.setContentsMargins(10, 0, 0, 0)
        else:
            self._title_label.setVisible(False)
            
        # 连接父窗口的标题改变信号
        if parent:
            parent.windowTitleChanged.connect(self._on_window_title_changed)
        
        # 添加到左侧布局
        left_layout.addLayout(self._create_vlayout(self._route_back_button))
        left_layout.addLayout(self._create_vlayout(self._route_forward_button))
        left_layout.addLayout(self._create_vlayout(self._navigation_button))
        left_layout.addLayout(self._icon_label_layout)
        left_layout.addLayout(self._title_label_layout)
        
        self._main_layout.addLayout(left_layout)
        self._main_layout.addStretch()
        
        # --- 右侧布局 ---
        right_layout = QHBoxLayout()
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignRight)
        
        # 主题切换按钮
        self._theme_button = ElaToolButton(self)
        self._theme_button.set_ela_icon(ElaIconType.MoonStars)
        self._theme_button.setFixedSize(40, 30)
        self._theme_button.clicked.connect(self.themeChangeButtonClicked)
        
        # 最小化按钮
        self._min_button = ElaToolButton(self)
        self._min_button.set_ela_icon(ElaIconType.Dash)
        self._min_button.setFixedSize(40, 30)
        self._min_button.clicked.connect(self._on_min_clicked)
        
        # 最大化按钮
        self._max_button = ElaToolButton(self)
        self._max_button.set_ela_icon(ElaIconType.Square)
        self._max_button.setFixedSize(40, 30)
        self._max_button.clicked.connect(self._on_max_clicked)
        
        # 关闭按钮
        self._close_button = ElaIconButton(ElaIconType.Xmark, 18, 40, 30, self)
        self._close_button.set_light_hover_color(QColor(0xE8, 0x11, 0x23))
        self._close_button.set_dark_hover_color(QColor(0xE8, 0x11, 0x23))
        self._close_button.set_light_hover_icon_color(Qt.white)
        self._close_button.set_dark_hover_icon_color(Qt.white)
        self._close_button.clicked.connect(self._on_close_clicked)
        
        # 添加到右侧布局
        right_layout.addLayout(self._create_vlayout(self._theme_button))
        right_layout.addLayout(self._create_vlayout(self._min_button))
        right_layout.addLayout(self._create_vlayout(self._max_button))
        right_layout.addLayout(self._create_vlayout(self._close_button))
        
        self._main_layout.addLayout(right_layout)
        
        # 初始化主题样式
        self._update_icons()
        self._update_style()
        ela_theme.theme_mode_changed.connect(self._update_icons)
        ela_theme.theme_mode_changed.connect(self._update_style)

    def _create_vlayout(self, widget):
        """创建垂直布局包装器用于按钮居中"""
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(widget)
        layout.addStretch()
        return layout

    def _on_window_icon_changed(self, icon):
        """父窗口图标改变时更新图标标签"""
        self._icon_label.setPixmap(icon.pixmap(18, 18))
        self._icon_label.setVisible(not icon.isNull())
        self._icon_label_layout.setContentsMargins(0 if icon.isNull() else 10, 0, 0, 0)
        
    def _on_window_title_changed(self, title):
        """父窗口标题改变时更新标题标签"""
        self._title_label.setText(title)
        self._title_label.setVisible(bool(title))
        self._title_label_layout.setContentsMargins(0 if not title else 10, 0, 0, 0)

    def _update_style(self, mode=None):
        """根据主题更新标题颜色"""
        color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicText)
        self._title_label.setStyleSheet(f"QLabel {{ color: {color.name()}; }}")

    def _update_icons(self, mode=None):
        """根据当前主题更新主题按钮图标"""
        if ela_theme.get_theme_mode() == ElaThemeType.ThemeMode.Light:
             self._theme_button.set_ela_icon(ElaIconType.MoonStars)
        else:
             self._theme_button.set_ela_icon(ElaIconType.Sun)

    def _on_min_clicked(self):
        """最小化窗口"""
        if self.window():
            self.window().showMinimized()

    def _on_max_clicked(self):
        """切换窗口最大化/还原状态"""
        if self.window():
            if self.window().isMaximized():
                self.window().showNormal()
                self._max_button.set_ela_icon(ElaIconType.Square)
            else:
                self.window().showMaximized()
                self._max_button.set_ela_icon(ElaIconType.WindowRestore)

    def _on_close_clicked(self):
        """关闭窗口"""
        self.closeButtonClicked.emit()
        if self.window():
            self.window().close()
    
    def setWindowTitle(self, title):
        """设置在应用栏中显示的标题"""
        self._title_label.setText(title)
        self._title_label.setVisible(bool(title))
        self._title_label_layout.setContentsMargins(0 if not title else 10, 0, 0, 0)

    def mousePressEvent(self, event):
        """启用窗口拖拽"""
        if event.button() == Qt.LeftButton:
            if self.window() and self.window().windowHandle():
                self.window().windowHandle().startSystemMove()
        super().mousePressEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        """双击切换最大化/还原"""
        if event.button() == Qt.LeftButton:
            self._on_max_clicked()
        super().mouseDoubleClickEvent(event)
