from PySide6.QtCore import QObject, Signal

class ThemeService(QObject):
    """主题服务，管理应用的配色方案"""
    theme_changed = Signal(dict)
    
    _LIGHT_THEME = {
        "name": "light",
        "bg_main": "#f8f9fa",
        "bg_sec": "#ffffff",
        "bg_ter": "#f1f3f4",
        "text_main": "#202124",
        "text_sec": "#5f6368",
        "accent": "#1a73e8",
        "border": "#dadce0",
        "danger": "#d93025",
        "scroll_handle": "#bdc1c6"
    }

    _DARK_THEME = {
        "name": "dark",
        "bg_main": "#1e1e1e",
        "bg_sec": "#252525",
        "bg_ter": "#2d2d2d",
        "text_main": "#e8eaed",
        "text_sec": "#9aa0a6",
        "accent": "#8ab4f8",
        "border": "#3c4043",
        "danger": "#f28b82",
        "scroll_handle": "#5f6368"
    }

    def __init__(self):
        super().__init__()
        self._current_theme = self._DARK_THEME

    def get_theme(self):
        return self._current_theme

    def toggle_theme(self):
        self._current_theme = self._DARK_THEME if self._current_theme["name"] == "light" else self._LIGHT_THEME
        self.theme_changed.emit(self._current_theme)

theme_service = ThemeService()
