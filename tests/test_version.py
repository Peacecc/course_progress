"""测试 app/version.py — 纯逻辑，无需任何 mock"""

from version import (
    __version__, __author__, __app_name__,
    VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH,
    VERSION_PRERELEASE, VERSION_DESCRIPTION,
    get_version_string, get_version_info,
)


class TestVersionConstants:
    """版本常量测试"""

    def test_app_name(self):
        assert __app_name__ == "CourseFlow"

    def test_version_string_format(self):
        assert __version__ == "0.1.1-alpha"

    def test_version_major_type(self):
        assert isinstance(VERSION_MAJOR, int)

    def test_version_minor_type(self):
        assert isinstance(VERSION_MINOR, int)

    def test_version_patch_type(self):
        assert isinstance(VERSION_PATCH, int)

    def test_prerelease_not_empty(self):
        assert len(VERSION_PRERELEASE) > 0

    def test_description_not_empty(self):
        assert len(VERSION_DESCRIPTION) > 0


class TestGetVersionString:
    """get_version_string() 测试"""

    def test_returns_string(self):
        result = get_version_string()
        assert isinstance(result, str)

    def test_contains_app_name(self):
        assert __app_name__ in get_version_string()

    def test_contains_version(self):
        assert __version__ in get_version_string()

    def test_format_is_name_v_version(self):
        assert get_version_string() == f"{__app_name__} v{__version__}"


class TestGetVersionInfo:
    """get_version_info() 测试"""

    def test_returns_dict(self):
        assert isinstance(get_version_info(), dict)

    def test_has_all_keys(self):
        info = get_version_info()
        expected_keys = {
            "app_name", "version", "major", "minor",
            "patch", "prerelease", "description", "author",
        }
        assert set(info.keys()) == expected_keys

    def test_values_match_constants(self):
        info = get_version_info()
        assert info["app_name"] == __app_name__
        assert info["version"] == __version__
        assert info["major"] == VERSION_MAJOR
        assert info["minor"] == VERSION_MINOR
        assert info["patch"] == VERSION_PATCH
        assert info["prerelease"] == VERSION_PRERELEASE
        assert info["description"] == VERSION_DESCRIPTION
        assert info["author"] == __author__

    def test_semver_consistency(self):
        """__version__ 与 VERSION_MAJOR.MINOR.PATCH-PRERELEASE 一致"""
        expected = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}-{VERSION_PRERELEASE}"
        assert __version__ == expected
