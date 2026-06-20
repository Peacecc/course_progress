"""主题服务 — 管理应用的浅色/深色配色方案，通过 Qt Signal 通知所有订阅组件"""

from PySide6.QtCore import QObject, Signal


class ThemeService(QObject):
    """主题服务单例，所有需要响应主题变更的组件通过 theme_changed 信号订阅"""

    theme_changed = Signal(dict)

    # ---- 浅色主题 Token ----
    LIGHT_THEME = {
        "name": "light",
        "bg_main": "#f8f9fa",
        "bg_sec": "#ffffff",
        "bg_ter": "#f1f3f4",
        "text_main": "#202124",
        "text_sec": "#5f6368",
        "accent": "#0078D4",
        "border": "#dadce0",
        "danger": "#d93025",
        "scroll_handle": "#bdc1c6",
    }

    # ---- 深色主题 Token ----
    DARK_THEME = {
        "name": "dark",
        "bg_main": "#1e1e1e",
        "bg_sec": "#252525",
        "bg_ter": "#2d2d2d",
        "text_main": "#e8eaed",
        "text_sec": "#9aa0a6",
        "accent": "#0078D4",
        "border": "#3c4043",
        "danger": "#f28b82",
        "scroll_handle": "#5f6368",
    }

    def __init__(self, initial_theme: str = "dark"):
        """
        初始化主题服务。

        Args:
            initial_theme: 初始主题名称，"dark" 或 "light"
        """
        super().__init__()
        self._current_theme = self.DARK_THEME if initial_theme == "dark" else self.LIGHT_THEME

    # ---- 公共接口 ----

    def get_theme(self) -> dict:
        """获取当前主题的颜色 Token 字典"""
        return dict(self._current_theme)

    def get_theme_name(self) -> str:
        """获取当前主题名称"""
        return self._current_theme["name"]

    def set_theme(self, name: str):
        """
        设置主题。

        Args:
            name: "dark" 或 "light"
        """
        new_theme = self.DARK_THEME if name == "dark" else self.LIGHT_THEME
        if new_theme["name"] != self._current_theme["name"]:
            self._current_theme = new_theme
            self.theme_changed.emit(self.get_theme())

    def toggle_theme(self):
        """切换浅色/深色主题"""
        self.set_theme("light" if self._current_theme["name"] == "dark" else "dark")

    def is_dark(self) -> bool:
        """当前是否为深色主题"""
        return self._current_theme["name"] == "dark"


# 全局单例 — 由 main.py 在启动时创建，其他模块通过 import 获取引用
# 注意：这个单例在模块首次 import 时就会创建
theme_service = ThemeService()
