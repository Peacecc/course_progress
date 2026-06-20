"""测试 app/services/theme_service.py — 需要 QApplication"""

import pytest
from services.theme_service import ThemeService


class TestThemeServiceInit:
    """ThemeService 初始化测试"""

    def test_default_theme_is_dark(self, qapp):
        ts = ThemeService()
        assert ts.get_theme_name() == "dark"
        assert ts.is_dark() is True

    def test_light_theme_initial(self, qapp):
        ts = ThemeService(initial_theme="light")
        assert ts.get_theme_name() == "light"
        assert ts.is_dark() is False

    def test_initial_theme_invalid_defaults_to_light(self, qapp):
        """非 'dark' 的 initial_theme 默认为 light"""
        ts = ThemeService(initial_theme="invalid")
        assert ts.get_theme_name() == "light"


class TestThemeTokens:
    """主题色 Token 测试"""

    REQUIRED_KEYS = {
        "name", "bg_main", "bg_sec", "bg_ter",
        "text_main", "text_sec", "accent", "border",
        "danger", "scroll_handle",
    }

    def test_light_theme_has_all_keys(self):
        assert set(ThemeService.LIGHT_THEME.keys()) == self.REQUIRED_KEYS

    def test_dark_theme_has_all_keys(self):
        assert set(ThemeService.DARK_THEME.keys()) == self.REQUIRED_KEYS

    def test_light_theme_name(self):
        assert ThemeService.LIGHT_THEME["name"] == "light"

    def test_dark_theme_name(self):
        assert ThemeService.DARK_THEME["name"] == "dark"

    def test_accent_is_same_in_both(self):
        assert ThemeService.LIGHT_THEME["accent"] == ThemeService.DARK_THEME["accent"]

    def test_all_tokens_are_strings(self):
        for theme in [ThemeService.LIGHT_THEME, ThemeService.DARK_THEME]:
            for key, value in theme.items():
                assert isinstance(value, str), f"{key} = {value!r} not a string"


class TestGetTheme:
    """get_theme() 测试"""

    def test_returns_dict(self, qapp):
        ts = ThemeService()
        theme = ts.get_theme()
        assert isinstance(theme, dict)

    def test_returns_copy_not_reference(self, qapp):
        ts = ThemeService()
        theme1 = ts.get_theme()
        theme2 = ts.get_theme()
        theme1["accent"] = "#FF0000"
        assert theme2["accent"] != "#FF0000"

    def test_has_all_required_keys(self, qapp):
        ts = ThemeService()
        theme = ts.get_theme()
        assert set(theme.keys()) == TestThemeTokens.REQUIRED_KEYS


class TestSetTheme:
    """set_theme() 测试"""

    def test_set_to_light(self, qapp):
        ts = ThemeService()
        ts.set_theme("light")
        assert ts.get_theme_name() == "light"
        assert ts.is_dark() is False

    def test_set_to_dark(self, qapp):
        ts = ThemeService(initial_theme="light")
        ts.set_theme("dark")
        assert ts.get_theme_name() == "dark"
        assert ts.is_dark() is True

    def test_set_same_no_signal(self, qapp):
        ts = ThemeService()
        signal_count = 0
        ts.theme_changed.connect(lambda _: None)

        # 使用 qtbot 或手动追踪
        emitted = []
        ts.theme_changed.connect(lambda t: emitted.append(t))

        ts.set_theme("dark")  # 已经是 dark，不应触发
        assert len(emitted) == 0

    def test_set_different_emits_signal(self, qapp):
        ts = ThemeService()
        emitted = []
        ts.theme_changed.connect(lambda t: emitted.append(t))

        ts.set_theme("light")
        assert len(emitted) == 1
        assert emitted[0]["name"] == "light"

    def test_signal_carries_full_theme(self, qapp):
        ts = ThemeService()
        emitted = []
        ts.theme_changed.connect(lambda t: emitted.append(t))

        ts.set_theme("light")
        assert set(emitted[0].keys()) == TestThemeTokens.REQUIRED_KEYS


class TestToggleTheme:
    """toggle_theme() 测试"""

    def test_dark_to_light(self, qapp):
        ts = ThemeService()
        ts.toggle_theme()
        assert ts.get_theme_name() == "light"

    def test_light_to_dark(self, qapp):
        ts = ThemeService(initial_theme="light")
        ts.toggle_theme()
        assert ts.get_theme_name() == "dark"

    def test_toggle_emits_signal(self, qapp):
        ts = ThemeService()
        emitted = []
        ts.theme_changed.connect(lambda t: emitted.append(t))
        ts.toggle_theme()
        assert len(emitted) == 1


class TestIsDark:
    """is_dark() 测试"""

    def test_dark_theme(self, qapp):
        assert ThemeService().is_dark() is True

    def test_light_theme(self, qapp):
        assert ThemeService(initial_theme="light").is_dark() is False
