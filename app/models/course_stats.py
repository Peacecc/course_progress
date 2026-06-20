"""课程统计数据容器 — 统一 View 层所需的所有计算字段"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class CourseStats:
    """一门课程的统计数据，由 DataManager/Controller 统一计算，View 直接使用"""

    # 视频进度
    total_videos: int = 0
    completed_videos: int = 0
    remaining_videos: int = 0

    # 时长统计（秒）
    total_duration_sec: float = 0.0
    watched_duration_sec: float = 0.0

    # 今日统计（秒）
    today_watched_sec: float = 0.0
    today_plan_sec: float = 0.0

    # 学习余额（分钟，正=超前，负=落后）
    balance_minutes: float = 0.0

    # 实际累计与计划累计（分钟，用于调试）
    actual_total_minutes: float = 0.0
    plan_total_minutes: float = 0.0

    # 完成百分比 (0-100)
    progress_percent: float = 0.0

    # 预计完成日期
    estimated_finish_date: str = "--"

    # 连续学习天数（activity_log 中的连续天数）
    streak_days: int = 0

    # ---- 派生属性 ----

    @property
    def total_hours(self) -> float:
        """总时长（小时）"""
        return self.total_duration_sec / 3600.0

    @property
    def watched_hours(self) -> float:
        """已观看时长（小时）"""
        return self.watched_duration_sec / 3600.0

    @property
    def today_watched_hours(self) -> float:
        """今日观看时长（小时）"""
        return self.today_watched_sec / 3600.0

    @property
    def today_plan_hours(self) -> float:
        """今日计划时长（小时）"""
        return self.today_plan_sec / 3600.0

    @property
    def is_completed(self) -> bool:
        """课程是否全部完成"""
        return self.completed_videos >= self.total_videos > 0

    @property
    def balance_hours(self) -> float:
        """学习余额（小时）"""
        return self.balance_minutes / 60.0


@dataclass
class CourseCardData:
    """首页课程卡片所需的展示数据（轻量，不包含完整 Course 对象）"""

    course_id: str = ""
    course_name: str = ""
    progress_percent: float = 0.0

    # 时长显示（秒 → 由 View 格式化）
    watched_sec: float = 0.0
    total_sec: float = 0.0

    # 今日显示
    today_watched_sec: float = 0.0
    today_plan_sec: float = 0.0

    # 余额（分钟）
    balance_minutes: float = 0.0

    # 预计剩余天数
    remaining_days: int = 0


@dataclass
class DashboardData:
    """课程看板所需的全部数据"""

    # 基本统计
    total_videos: int = 0
    completed_videos: int = 0
    total_hours: float = 0.0
    watched_hours: float = 0.0

    # 今日
    today_hours: float = 0.0
    plan_today_hours: float = 0.0

    # 余额
    balance_hours: float = 0.0

    # 预计完成
    estimated_finish_str: str = "--"

    # 开始日期（ISO 格式字符串）
    start_date_iso: str = ""

    # 周计划
    weekly_schedule: list = field(default_factory=lambda: [0.0] * 7)

    # 每日统计（用于热力图）
    daily_stats: dict = field(default_factory=dict)
