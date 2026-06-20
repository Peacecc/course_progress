"""测试 app/models/course_stats.py — 纯数据类，无副作用"""

from models.course_stats import CourseStats, CourseCardData, DashboardData


class TestCourseStats:
    """CourseStats 数据类测试"""

    def test_defaults_all_zero(self):
        stats = CourseStats()
        assert stats.total_videos == 0
        assert stats.completed_videos == 0
        assert stats.remaining_videos == 0
        assert stats.total_duration_sec == 0.0
        assert stats.watched_duration_sec == 0.0
        assert stats.today_watched_sec == 0.0
        assert stats.today_plan_sec == 0.0
        assert stats.balance_minutes == 0.0
        assert stats.actual_total_minutes == 0.0
        assert stats.plan_total_minutes == 0.0
        assert stats.progress_percent == 0.0
        assert stats.estimated_finish_date == "--"
        assert stats.streak_days == 0

    def test_field_assignment(self):
        stats = CourseStats(
            total_videos=10,
            completed_videos=5,
            remaining_videos=5,
            total_duration_sec=7200.0,
            watched_duration_sec=3600.0,
            today_watched_sec=1800.0,
            today_plan_sec=3600.0,
            balance_minutes=30.0,
            actual_total_minutes=120.0,
            plan_total_minutes=90.0,
            progress_percent=50.0,
            estimated_finish_date="2026-07-01",
            streak_days=7,
        )
        assert stats.total_videos == 10
        assert stats.completed_videos == 5
        assert stats.watched_duration_sec == 3600.0
        assert stats.progress_percent == 50.0
        assert stats.streak_days == 7

    # ---- 派生属性 ----

    def test_total_hours(self):
        stats = CourseStats(total_duration_sec=7200.0)
        assert stats.total_hours == 2.0

    def test_total_hours_zero(self):
        stats = CourseStats(total_duration_sec=0)
        assert stats.total_hours == 0.0

    def test_watched_hours(self):
        stats = CourseStats(watched_duration_sec=5400.0)
        assert stats.watched_hours == 1.5

    def test_today_watched_hours(self):
        stats = CourseStats(today_watched_sec=1800.0)
        assert stats.today_watched_hours == 0.5

    def test_today_plan_hours(self):
        stats = CourseStats(today_plan_sec=7200.0)
        assert stats.today_plan_hours == 2.0

    def test_is_completed_true(self):
        stats = CourseStats(total_videos=5, completed_videos=5)
        assert stats.is_completed is True

    def test_is_completed_false(self):
        stats = CourseStats(total_videos=5, completed_videos=4)
        assert stats.is_completed is False

    def test_is_completed_zero_total(self):
        """total_videos=0 时即使 completed 也为 0，不应报 completed"""
        stats = CourseStats(total_videos=0, completed_videos=0)
        assert stats.is_completed is False

    def test_balance_hours(self):
        stats = CourseStats(balance_minutes=90.0)
        assert stats.balance_hours == 1.5

    def test_balance_hours_negative(self):
        stats = CourseStats(balance_minutes=-60.0)
        assert stats.balance_hours == -1.0


class TestCourseCardData:
    """CourseCardData 数据类测试"""

    def test_defaults(self):
        card = CourseCardData()
        assert card.course_id == ""
        assert card.course_name == ""
        assert card.progress_percent == 0.0
        assert card.watched_sec == 0.0
        assert card.total_sec == 0.0
        assert card.today_watched_sec == 0.0
        assert card.today_plan_sec == 0.0
        assert card.balance_minutes == 0.0
        assert card.remaining_days == 0

    def test_full_construction(self):
        card = CourseCardData(
            course_id="abc-123",
            course_name="Machine Learning",
            progress_percent=63.5,
            watched_sec=5000.0,
            total_sec=8000.0,
            today_watched_sec=1200.0,
            today_plan_sec=3600.0,
            balance_minutes=45.0,
            remaining_days=15,
        )
        assert card.course_id == "abc-123"
        assert card.course_name == "Machine Learning"
        assert card.progress_percent == 63.5
        assert card.remaining_days == 15


class TestDashboardData:
    """DashboardData 数据类测试"""

    def test_defaults(self):
        dash = DashboardData()
        assert dash.total_videos == 0
        assert dash.completed_videos == 0
        assert dash.total_hours == 0.0
        assert dash.watched_hours == 0.0
        assert dash.today_hours == 0.0
        assert dash.plan_today_hours == 0.0
        assert dash.balance_hours == 0.0
        assert dash.estimated_finish_str == "--"
        assert dash.start_date_iso == ""

    def test_weekly_schedule_default(self):
        """默认 weekly_schedule 是 7 个 0.0"""
        dash = DashboardData()
        assert dash.weekly_schedule == [0.0] * 7
        assert len(dash.weekly_schedule) == 7

    def test_daily_stats_default(self):
        """默认 daily_stats 是空 dict"""
        dash = DashboardData()
        assert dash.daily_stats == {}

    def test_custom_weekly_schedule(self):
        schedule = [1.0, 2.0, 0.0, 1.5, 0.0, 3.0, 0.0]
        dash = DashboardData(weekly_schedule=schedule)
        assert dash.weekly_schedule == schedule

    def test_daily_stats_independent(self):
        """daily_stats 是独立字典，不共享可变引用"""
        dash1 = DashboardData()
        dash2 = DashboardData()
        dash1.daily_stats["2026-06-20"] = 3600
        assert "2026-06-20" not in dash2.daily_stats
