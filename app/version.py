"""版本信息模块 — 遵循语义化版本控制 (SemVer)

版本号格式: 主版本号.次版本号.修订号[-预发布标识]
参考文档: doc/Version_Define.md
"""

__version__ = "0.1.1-alpha"
__author__ = "CourseFlow Team"
__app_name__ = "CourseFlow"

# 版本详情
VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_PATCH = 1
VERSION_PRERELEASE = "alpha"  # 开发阶段: alpha → beta → rc → (正式版省略)

# 版本描述
VERSION_DESCRIPTION = "课程卡片重构 — 多列网格布局、accent 主题色悬停高亮、垃圾桶删除、窗口四边四角缩放"


def get_version_string() -> str:
    """返回完整的版本字符串"""
    return f"{__app_name__} v{__version__}"


def get_version_info() -> dict:
    """返回版本信息字典"""
    return {
        "app_name": __app_name__,
        "version": __version__,
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "prerelease": VERSION_PRERELEASE,
        "description": VERSION_DESCRIPTION,
        "author": __author__,
    }
