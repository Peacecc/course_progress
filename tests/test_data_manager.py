"""测试 app/models/data_manager.py — 核心业务逻辑，需要 mock 时间和文件系统"""

import json
from unittest.mock import ANY

import pytest


@pytest.fixture
def frozen_time(monkeypatch):
    """冻结 datetime.now() 和 date.today()"""
    from datetime import datetime, date

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 6, 20, 12, 0, 0)

    class FrozenDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 6, 20)

    monkeypatch.setattr("models.data_manager.datetime", FrozenDateTime)
    monkeypatch.setattr("models.data_manager.date", FrozenDate)
    return FrozenDateTime, FrozenDate


@pytest.fixture
def dm(tmp_data_dir, tmp_courses_json, frozen_time):
    """创建 DataManager 实例，使用临时数据目录和冻结时间"""
    from models.data_manager import DataManager
    return DataManager()


class TestDataManagerInit:
    """DataManager 初始化测试"""

    def test_init_loads_data(self, dm):
        assert dm.data == {"courses": []}

    def test_init_migrates_missing_fields(self, tmp_data_dir, frozen_time):
        """旧格式数据缺少字段时自动补全"""
        from models.data_manager import DataManager
        from utils.paths import PathManager

        # 写入缺少字段的旧格式数据
        PathManager.COURSES_JSON.parent.mkdir(parents=True, exist_ok=True)
        old_data = {
            "courses": [{
                "id": "old-course",
                "name": "Old",
                "path": "/tmp/old",
                "added_at": "2026-01-01",
                "total_videos": 1,
                "total_duration": 100,
                "videos": [{
                    "rel_path": "v.mp4",
                    "duration": 100,
                }]
            }]
        }
        PathManager.COURSES_JSON.write_text(json.dumps(old_data), encoding="utf-8")

        dm = DataManager()
        course = dm.get_course_by_id("old-course")
        assert course is not None
        assert "daily_stats" in course
        assert "weekly_schedule" in course
        assert "start_date" in course
        for v in course["videos"]:
            assert "watched_duration" in v
            assert "completed" in v
            assert "last_watched" in v


class TestCourseCRUD:
    """课程增删改查测试"""

    def test_add_course_returns_dict(self, dm):
        course = dm.add_course("Test", "/test/path", [], {"total_videos": 0, "total_duration": 0})
        assert isinstance(course, dict)
        assert course["name"] == "Test"
        assert course["path"] == "/test/path"
        assert isinstance(course["id"], str)
        assert len(course["id"]) > 0

    def test_add_course_appears_in_get_courses(self, dm):
        dm.add_course("ML", "/ml", [], {"total_videos": 0, "total_duration": 0})
        courses = dm.get_courses()
        assert len(courses) == 1
        assert courses[0]["name"] == "ML"

    def test_add_course_with_videos(self, dm):
        videos_data = [
            {"rel_path": "01.mp4", "abs_path": "/test/01.mp4", "duration": 300.0},
            {"rel_path": "02.mp4", "abs_path": "/test/02.mp4", "duration": 600.0},
        ]
        stats = {"total_videos": 2, "total_duration": 900.0}
        course = dm.add_course("Video Course", "/test", videos_data, stats)

        assert course["total_videos"] == 2
        assert course["total_duration"] == 900.0
        assert len(course["videos"]) == 2
        assert course["videos"][0]["rel_path"] == "01.mp4"
        assert course["videos"][0]["duration"] == 300.0
        assert course["videos"][0]["watched_duration"] == 0
        assert course["videos"][0]["completed"] is False

    def test_get_course_by_id_found(self, dm):
        course = dm.add_course("Found", "/f", [], {"total_videos": 0, "total_duration": 0})
        result = dm.get_course_by_id(course["id"])
        assert result is not None
        assert result["name"] == "Found"

    def test_get_course_by_id_not_found(self, dm):
        assert dm.get_course_by_id("nonexistent") is None

    def test_delete_course_removes(self, dm):
        course = dm.add_course("Gone", "/gone", [], {"total_videos": 0, "total_duration": 0})
        assert len(dm.get_courses()) == 1
        dm.delete_course(course["id"])
        assert len(dm.get_courses()) == 0

    def test_delete_nonexistent_does_not_crash(self, dm):
        dm.delete_course("nonexistent")  # 不应抛异常

    def test_update_course_name(self, dm):
        course = dm.add_course("Old Name", "/x", [], {"total_videos": 0, "total_duration": 0})
        dm.update_course_name(course["id"], "New Name")
        updated = dm.get_course_by_id(course["id"])
        assert updated["name"] == "New Name"

    def test_update_name_nonexistent_does_not_crash(self, dm):
        dm.update_course_name("nonexistent", "whatever")  # 不应抛异常


class TestPersistence:
    """数据持久化测试"""

    def test_data_persists_to_disk(self, dm):
        """添加课程后数据写入 JSON 文件"""
        dm.add_course("Persist", "/p", [], {"total_videos": 0, "total_duration": 0})
        dm.add_course("Persist2", "/p2", [], {"total_videos": 0, "total_duration": 0})

        from utils.paths import PathManager
        assert PathManager.COURSES_JSON.exists()
        with open(PathManager.COURSES_JSON, "r", encoding="utf-8") as f:
            saved = json.load(f)

        assert len(saved["courses"]) == 2
        names = {c["name"] for c in saved["courses"]}
        assert names == {"Persist", "Persist2"}

    def test_data_reloads_correctly(self, dm, tmp_courses_json, frozen_time):
        """重新创建 DataManager 应加载已保存的数据"""
        dm.add_course("Reload Test", "/r", [], {"total_videos": 0, "total_duration": 0})
        cid = dm.get_courses()[0]["id"]

        # 重新构造
        from models.data_manager import DataManager
        dm2 = DataManager()
        assert len(dm2.get_courses()) == 1
        assert dm2.get_course_by_id(cid) is not None


class TestVideoProgress:
    """视频进度更新测试"""

    def test_update_video_progress(self, dm):
        course = dm.add_course("Prog", "/prog",
                               [{"rel_path": "v1.mp4", "abs_path": "/prog/v1.mp4", "duration": 600.0}],
                               {"total_videos": 1, "total_duration": 600.0})

        dm.update_video_progress(course["id"], "v1.mp4", watched_duration=300.0, completed=False)

        updated = dm.get_course_by_id(course["id"])
        video = updated["videos"][0]
        assert video["watched_duration"] == 300.0
        assert video["completed"] is False
        assert video["last_watched"] is not None

    def test_update_video_progress_completed(self, dm):
        course = dm.add_course("Done", "/done",
                               [{"rel_path": "v.mp4", "abs_path": "/done/v.mp4", "duration": 120.0}],
                               {"total_videos": 1, "total_duration": 120.0})

        dm.update_video_progress(course["id"], "v.mp4", watched_duration=120.0, completed=True)

        updated = dm.get_course_by_id(course["id"])
        assert updated["videos"][0]["completed"] is True

    def test_update_progress_nonexistent_course(self, dm):
        """不存在的课程不抛异常"""
        dm.update_video_progress("nonexistent", "v.mp4", 100.0, False)

    def test_update_progress_daily_stats(self, dm):
        """更新进度后 daily_stats 记录增量"""
        course = dm.add_course("Daily", "/d",
                               [{"rel_path": "v.mp4", "abs_path": "/d/v.mp4", "duration": 3600.0}],
                               {"total_videos": 1, "total_duration": 3600.0})

        # 第一次观看 1800 秒
        dm.update_video_progress(course["id"], "v.mp4", watched_duration=1800.0, completed=False)
        stats = dm.get_course_by_id(course["id"])["daily_stats"]
        assert stats.get("2026-06-20", 0) == 1800.0

        # 继续观看 600 秒（增量 600）
        dm.update_video_progress(course["id"], "v.mp4", watched_duration=2400.0, completed=False)
        stats = dm.get_course_by_id(course["id"])["daily_stats"]
        assert stats.get("2026-06-20", 0) == 2400.0


class TestLearningPlan:
    """学习计划测试"""

    def test_set_weekly_schedule(self, dm):
        course = dm.add_course("Plan", "/plan", [], {"total_videos": 0, "total_duration": 0})
        schedule = [1.0, 2.0, 0.0, 1.5, 0.0, 3.0, 0.0]
        dm.set_weekly_schedule(course["id"], schedule, "2026-06-01")

        updated = dm.get_course_by_id(course["id"])
        assert updated["weekly_schedule"] == schedule
        assert updated["start_date"] == "2026-06-01"

    def test_get_today_plan_seconds(self, dm):
        """2026-06-20 是周六（weekday=5），计划为 3.0 小时"""
        course = dm.add_course("TodayPlan", "/tp", [], {"total_videos": 0, "total_duration": 0})
        # weekday 0=Mon, 5=Sat, schedule[5]=3.0
        schedule = [0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 0.0]
        dm.set_weekly_schedule(course["id"], schedule, "2026-06-01")

        plan_sec = dm.get_today_plan_seconds(course["id"])
        assert plan_sec == 3.0 * 3600.0  # 10800 秒

    def test_get_today_plan_nonexistent(self, dm):
        assert dm.get_today_plan_seconds("nonexistent") == 0.0

    def test_get_today_progress(self, dm):
        course = dm.add_course("TodayProg", "/tprog",
                               [{"rel_path": "v.mp4", "abs_path": "/tprog/v.mp4", "duration": 3600.0}],
                               {"total_videos": 1, "total_duration": 3600.0})
        dm.update_video_progress(course["id"], "v.mp4", watched_duration=900.0, completed=False)

        assert dm.get_today_progress(course["id"]) == 900.0

    def test_get_today_progress_nonexistent(self, dm):
        assert dm.get_today_progress("nonexistent") == 0.0


class TestCourseBalance:
    """学习余额计算测试"""

    def test_no_start_date_returns_zero(self, dm):
        course = dm.add_course("NoStart", "/ns", [], {"total_videos": 0, "total_duration": 0})
        bal, act, plan = dm.get_course_balance(course["id"])
        assert bal == 0.0 and act == 0.0 and plan == 0.0

    def test_balance_with_plan(self, dm):
        """有计划和实际学习数据时正确计算余额"""
        course = dm.add_course("Bal", "/bal",
                               [{"rel_path": "v.mp4", "abs_path": "/bal/v.mp4", "duration": 7200.0}],
                               {"total_videos": 1, "total_duration": 7200.0})
        # 周计划：每天 1 小时，从 6 月 15 日开始
        schedule = [1.0] * 7  # 每天 1 小时
        dm.set_weekly_schedule(course["id"], schedule, "2026-06-15")

        # 模拟学习记录：6/15-6/20 共 6 天，每天学了 1.5 小时
        for day in range(15, 21):
            course["daily_stats"][f"2026-06-{day:02d}"] = 5400.0  # 1.5 hours

        bal, act, plan = dm.get_course_balance(course["id"])
        # 实际：6天 × 1.5h = 9h，计划：6天 × 1h = 6h，余额：9-6=3h = 180min
        assert bal == pytest.approx(180.0, rel=0.1)

    def test_future_start_date_returns_zero(self, dm):
        course = dm.add_course("Future", "/fut", [], {"total_videos": 0, "total_duration": 0})
        dm.set_weekly_schedule(course["id"], [1.0] * 7, "2026-07-01")  # 未到开始日
        bal, act, plan = dm.get_course_balance(course["id"])
        assert bal == 0.0


class TestRemainingDays:
    """剩余天数计算测试"""

    def test_completed_returns_zero(self, dm):
        course = dm.add_course("Comp", "/comp",
                               [{"rel_path": "v.mp4", "abs_path": "/comp/v.mp4", "duration": 100.0}],
                               {"total_videos": 1, "total_duration": 100.0})
        dm.update_video_progress(course["id"], "v.mp4", watched_duration=100.0, completed=True)
        assert dm.calculate_remaining_days(course["id"]) == 0

    def test_empty_course_returns_zero(self, dm):
        course = dm.add_course("Empty", "/empty", [], {"total_videos": 0, "total_duration": 0})
        assert dm.calculate_remaining_days(course["id"]) == 0

    def test_uses_plan_if_no_history(self, dm):
        """无历史数据时使用周计划推算"""
        course = dm.add_course("PlanOnly", "/po",
                               [{"rel_path": "v.mp4", "abs_path": "/po/v.mp4", "duration": 36000.0}],
                               {"total_videos": 1, "total_duration": 36000.0})  # 10h remaining
        schedule = [0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 0.0]  # 每周仅周六 5h
        dm.set_weekly_schedule(course["id"], schedule, "2026-06-01")
        # 每周 5h，平均每天 ~0.714h，10h 需要 ~14 天
        remaining = dm.calculate_remaining_days(course["id"])
        assert remaining > 0
        assert remaining <= 20  # 合理范围

    def test_uses_history_if_available(self, dm):
        """有学习历史时使用平均速度"""
        course = dm.add_course("WithHistory", "/wh",
                               [{"rel_path": "v.mp4", "abs_path": "/wh/v.mp4", "duration": 72000.0}],
                               {"total_videos": 1, "total_duration": 72000.0})  # 20h remaining
        # 10 天历史，每天 1 小时
        for day in range(10, 20):
            course["daily_stats"][f"2026-06-{day:02d}"] = 3600.0

        remaining = dm.calculate_remaining_days(course["id"])
        # 平均 1h/天，20h → ~20 天
        assert 15 <= remaining <= 25


class TestEstimateFinishDate:
    """预计完成日期测试"""

    def test_completed(self, dm):
        course = dm.add_course("Done", "/d",
                               [{"rel_path": "v.mp4", "abs_path": "/d/v.mp4", "duration": 100.0}],
                               {"total_videos": 1, "total_duration": 100.0})
        dm.update_video_progress(course["id"], "v.mp4", watched_duration=100.0, completed=True)
        assert dm.estimate_finish_date(course["id"]) == "已完成"

    def test_no_schedule_returns_dash(self, dm):
        course = dm.add_course("NoPlan", "/np",
                               [{"rel_path": "v.mp4", "abs_path": "/np/v.mp4", "duration": 3600.0}],
                               {"total_videos": 1, "total_duration": 3600.0})
        assert dm.estimate_finish_date(course["id"]) == "--"

    def test_with_plan_returns_date(self, dm):
        """有计划时返回合理日期"""
        course = dm.add_course("Planned", "/p",
                               [{"rel_path": "v.mp4", "abs_path": "/p/v.mp4", "duration": 18000.0}],
                               {"total_videos": 1, "total_duration": 18000.0})  # 5h
        schedule = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # 每周一 1h
        dm.set_weekly_schedule(course["id"], schedule, "2026-06-01")
        result = dm.estimate_finish_date(course["id"])
        assert result != "--"
        assert result != "已完成"
        # 应为未来日期
        assert result > "2026-06-20"


class TestSettings:
    """全局设置测试"""

    def test_get_setting_default(self, dm):
        assert dm.get_setting("theme", "dark") == "dark"

    def test_set_and_get_setting(self, dm):
        dm.set_setting("theme", "light")
        assert dm.get_setting("theme") == "light"

    def test_settings_persist(self, dm, frozen_time):
        dm.set_setting("lang", "zh")
        from models.data_manager import DataManager
        dm2 = DataManager()
        assert dm2.get_setting("lang") == "zh"


class TestStreak:
    """连续学习天数测试"""

    def test_no_activity_returns_zero(self, dm):
        course = dm.add_course("NoAct", "/na", [], {"total_videos": 0, "total_duration": 0})
        stats = dm.calculate_course_stats(course["id"])
        assert stats.streak_days == 0
