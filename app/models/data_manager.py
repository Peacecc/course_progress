"""数据管理器 — 课程数据的加载、保存和操作的唯一入口"""

import uuid
import logging
from datetime import datetime, timedelta, date
from pathlib import Path

from utils.paths import PathManager
from utils.atomic_write import atomic_write_json, safe_read_json
from utils.logger import setup_logger

logger = setup_logger("DataManager", PathManager.LOG_DIR)


class DataManager:
    """数据管理器，负责课程数据的加载、保存和操作（单一数据源）"""

    def __init__(self):
        """初始化数据管理器，自动加载数据并执行迁移"""
        PathManager.ensure_dirs()
        self.data_file = PathManager.COURSES_JSON
        self.data = self._load_data()
        self._migrate_data()
        logger.info(f"DataManager 初始化完成，已加载 {len(self.data.get('courses', []))} 门课程")

    # ==================== 数据加载/保存 ====================

    def _load_data(self) -> dict:
        """安全加载数据，文件不存在或损坏时返回默认结构"""
        return safe_read_json(self.data_file, default={"courses": []})

    def _save_data(self, data: dict = None):
        """原子保存数据到 JSON 文件"""
        if data is None:
            data = self.data
        try:
            atomic_write_json(self.data_file, data)
        except Exception as e:
            logger.error(f"数据保存失败: {e}")
            raise

    def _migrate_data(self):
        """数据迁移：补全旧版本缺失的字段"""
        migrated = False
        for course in self.data.get("courses", []):
            # 确保必要字段存在
            if "daily_stats" not in course:
                course["daily_stats"] = {}
                migrated = True
            if "weekly_schedule" not in course:
                course["weekly_schedule"] = [0.0] * 7
                migrated = True
            if "start_date" not in course:
                course["start_date"] = None
                migrated = True
            for video in course.get("videos", []):
                if "watched_duration" not in video:
                    video["watched_duration"] = 0
                    migrated = True
                if "completed" not in video:
                    video["completed"] = False
                    migrated = True
                if "last_watched" not in video:
                    video["last_watched"] = None
                    migrated = True
        if migrated:
            self._save_data()
            logger.info("数据迁移完成：已补全旧版本缺失字段")

    # ==================== 课程 CRUD ====================

    def add_course(self, name: str, path: str, videos_data: list, duration_stats: dict) -> dict:
        """
        添加新课程。

        Args:
            name: 课程名称
            path: 课程文件夹路径
            videos_data: 视频数据列表 [{"rel_path": ..., "abs_path": ..., "duration": ...}]
            duration_stats: {"total_videos": int, "total_duration": float}

        Returns:
            新创建的课程数据字典
        """
        course_id = str(uuid.uuid4())

        new_course = {
            "id": course_id,
            "name": name,
            "path": path,
            "added_at": datetime.now().isoformat(),
            "total_videos": duration_stats["total_videos"],
            "total_duration": duration_stats["total_duration"],
            "start_date": None,
            "weekly_schedule": [0.0] * 7,
            "daily_stats": {},
            "videos": [],
        }

        for v in videos_data:
            new_course["videos"].append({
                "rel_path": v["rel_path"],
                "duration": v["duration"],
                "watched_duration": 0,
                "completed": False,
                "last_watched": None,
            })

        self.data["courses"].append(new_course)
        self._save_data()
        logger.info(f"课程已添加: {name} ({len(videos_data)} 个视频)")
        return new_course

    def get_courses(self) -> list:
        """获取所有课程列表"""
        return self.data.get("courses", [])

    def get_course_by_id(self, course_id: str) -> dict | None:
        """根据 ID 获取课程，找不到返回 None"""
        for course in self.data.get("courses", []):
            if course["id"] == course_id:
                return course
        return None

    def delete_course(self, course_id: str):
        """删除课程及其所有数据"""
        before = len(self.data.get("courses", []))
        self.data["courses"] = [c for c in self.data.get("courses", []) if c["id"] != course_id]
        after = len(self.data["courses"])
        if before > after:
            self._save_data()
            logger.info(f"课程已删除: {course_id}")

    def update_course_name(self, course_id: str, new_name: str):
        """更新课程名称"""
        course = self.get_course_by_id(course_id)
        if course:
            course["name"] = new_name
            self._save_data()

    # ==================== 视频进度 ====================

    def update_video_progress(self, course_id: str, rel_path: str,
                               watched_duration: float, completed: bool):
        """
        更新视频观看进度。

        Args:
            course_id: 课程 ID
            rel_path: 视频相对路径
            watched_duration: 已观看时长（秒）
            completed: 是否已完成
        """
        course = self.get_course_by_id(course_id)
        if not course:
            return

        today_str = datetime.now().strftime("%Y-%m-%d")

        # 确保 daily_stats 存在
        if "daily_stats" not in course:
            course["daily_stats"] = {}

        for video in course["videos"]:
            if video["rel_path"] == rel_path:
                prev_watched = video.get("watched_duration", 0)

                # 增量更新每日统计
                if watched_duration > prev_watched:
                    delta = watched_duration - prev_watched
                    course["daily_stats"][today_str] = course["daily_stats"].get(today_str, 0) + delta
                    video["watched_duration"] = watched_duration

                # 标记完成
                if completed and not video.get("completed", False):
                    video["completed"] = True
                    self._log_activity()

                video["last_watched"] = datetime.now().isoformat()
                break

        self._save_data()

    def _log_activity(self):
        """记录每日活动（完成视频数）"""
        today = datetime.now().strftime("%Y-%m-%d")
        log = self.data.get("activity_log", {})
        log[today] = log.get(today, 0) + 1
        self.data["activity_log"] = log

    # ==================== 学习计划 ====================

    def set_weekly_schedule(self, course_id: str, schedule: list, start_date_iso: str):
        """设置课程的周计划和开始日期"""
        course = self.get_course_by_id(course_id)
        if course:
            course["weekly_schedule"] = list(schedule)
            course["start_date"] = start_date_iso
            self._save_data()

    def get_today_plan_seconds(self, course_id: str) -> float:
        """获取今日计划学习时长（秒）"""
        course = self.get_course_by_id(course_id)
        if not course:
            return 0.0
        schedule = course.get("weekly_schedule", [0] * 7)
        wd = datetime.now().weekday()
        return schedule[wd] * 3600.0

    def get_today_progress(self, course_id: str) -> float:
        """获取今日已学习时长（秒）"""
        course = self.get_course_by_id(course_id)
        if not course:
            return 0.0
        today_str = datetime.now().strftime("%Y-%m-%d")
        stats = course.get("daily_stats", {})
        return stats.get(today_str, 0.0)

    # ==================== 学习余额 ====================

    def get_course_balance(self, course_id: str) -> tuple:
        """
        计算学习余额（= 实际累计 - 计划累计）。

        Returns:
            (balance_minutes, actual_total_minutes, plan_total_minutes)
            余额 = 0 表示无开始日期或计划全为 0
        """
        course = self.get_course_by_id(course_id)
        if not course:
            return 0.0, 0.0, 0.0

        start_date_iso = course.get("start_date")
        if not start_date_iso:
            return 0.0, 0.0, 0.0

        try:
            start_date = datetime.fromisoformat(start_date_iso).date()
        except (ValueError, TypeError):
            return 0.0, 0.0, 0.0

        today = datetime.now().date()
        if today < start_date:
            return 0.0, 0.0, 0.0

        schedule = course.get("weekly_schedule", [0.0] * 7)
        if sum(schedule) < 0.1:
            return 0.0, 0.0, 0.0

        # 计算累计计划时长（小时）
        plan_total_hours = 0.0
        curr = start_date
        while curr <= today:
            wd = curr.weekday()
            plan_total_hours += schedule[wd]
            curr += timedelta(days=1)

        # 计算实际累计时长（小时）
        stats = course.get("daily_stats", {})
        actual_seconds = sum(stats.values())
        actual_total_hours = actual_seconds / 3600.0

        balance_hours = actual_total_hours - plan_total_hours
        return (
            balance_hours * 60.0,      # balance_minutes
            actual_total_hours * 60.0,  # actual_total_minutes
            plan_total_hours * 60.0,    # plan_total_minutes
        )

    # ==================== 剩余天数计算 ====================

    def calculate_remaining_days(self, course_id: str) -> int:
        """
        基于实际学习速度和周计划，估算完成剩余视频所需天数。

        优先使用历史平均速度；无历史数据则使用周计划推算。
        """
        course = self.get_course_by_id(course_id)
        if not course:
            return 0

        # 计算剩余时长（秒）
        remaining_sec = 0.0
        for v in course.get("videos", []):
            if not v.get("completed", False):
                remaining_sec += max(0, v.get("duration", 0) - v.get("watched_duration", 0))

        if remaining_sec <= 0:
            return 0

        # 策略 1：使用历史平均每日学习时长
        daily_stats = course.get("daily_stats", {})
        if daily_stats:
            values = list(daily_stats.values())
            avg_daily_sec = sum(values) / len(values)
            if avg_daily_sec > 60:  # 平均每天至少 1 分钟才有效
                return max(1, int(remaining_sec / avg_daily_sec + 0.5))

        # 策略 2：使用周计划平均每日时长
        schedule = course.get("weekly_schedule", [0] * 7)
        weekly_hours = sum(schedule)
        if weekly_hours > 0.1:
            avg_daily_hours = weekly_hours / 7.0
            avg_daily_sec = avg_daily_hours * 3600.0
            return max(1, int(remaining_sec / avg_daily_sec + 0.5))

        # 策略 3：兜底 — 假设每天 1 小时
        return max(1, int(remaining_sec / 3600.0 + 0.5))

    # ==================== 预计完成日期 ====================

    def estimate_finish_date(self, course_id: str) -> str:
        """
        根据周计划推算预计完成日期。

        Returns:
            日期字符串 (YYYY-MM-DD)，或 "--" (无计划/所有视频为空)，或 "已完成"
        """
        course = self.get_course_by_id(course_id)
        if not course:
            return "--"

        # 计算剩余时长
        remaining_hours = 0.0
        for v in course.get("videos", []):
            if not v.get("completed", False):
                remaining_hours += max(0, v.get("duration", 0) - v.get("watched_duration", 0)) / 3600.0

        if remaining_hours <= 0:
            return "已完成"

        schedule = course.get("weekly_schedule", [0] * 7)
        if sum(schedule) < 0.01:
            return "--"

        sim_date = date.today()
        needed = remaining_hours
        days_count = 0
        max_days = 365 * 5  # 防止无限循环

        while needed > 0 and days_count < max_days:
            day_wd = sim_date.weekday()
            day_plan = schedule[day_wd]
            needed -= day_plan
            if needed > 0:
                sim_date += timedelta(days=1)
            days_count += 1

        if days_count >= max_days:
            return "--"
        return sim_date.strftime("%Y-%m-%d")

    # ==================== 聚合统计 ====================

    def calculate_course_stats(self, course_id: str):
        """计算课程的完整统计数据，返回 CourseStats 实例"""
        from models.course_stats import CourseStats

        course = self.get_course_by_id(course_id)
        if not course:
            return CourseStats()

        videos = course.get("videos", [])
        total_v = len(videos)
        completed_v = sum(1 for v in videos if v.get("completed", False))
        total_dur = course.get("total_duration", 0)
        watched_dur = sum(v.get("watched_duration", 0) for v in videos)
        today_sec = self.get_today_progress(course_id)
        plan_sec = self.get_today_plan_seconds(course_id)
        bal_min, act_min, plan_min = self.get_course_balance(course_id)
        progress = (watched_dur / total_dur * 100) if total_dur > 0 else 0.0

        return CourseStats(
            total_videos=total_v,
            completed_videos=completed_v,
            remaining_videos=total_v - completed_v,
            total_duration_sec=total_dur,
            watched_duration_sec=watched_dur,
            today_watched_sec=today_sec,
            today_plan_sec=plan_sec,
            balance_minutes=bal_min,
            actual_total_minutes=act_min,
            plan_total_minutes=plan_min,
            progress_percent=round(progress, 1),
            estimated_finish_date=self.estimate_finish_date(course_id),
            streak_days=self._calculate_streak(),
        )

    def get_course_card_data(self):
        """获取所有课程的卡片展示数据列表"""
        from models.course_stats import CourseCardData

        cards = []
        for course in self.get_courses():
            stats = self.calculate_course_stats(course["id"])
            card = CourseCardData(
                course_id=course["id"],
                course_name=course["name"],
                progress_percent=stats.progress_percent,
                watched_sec=stats.watched_duration_sec,
                total_sec=stats.total_duration_sec,
                today_watched_sec=stats.today_watched_sec,
                today_plan_sec=stats.today_plan_sec,
                balance_minutes=stats.balance_minutes,
                remaining_days=self.calculate_remaining_days(course["id"]),
            )
            cards.append(card)
        return cards

    def get_dashboard_data(self, course_id: str):
        """获取课程看板的完整数据"""
        from models.course_stats import DashboardData

        course = self.get_course_by_id(course_id)
        if not course:
            return DashboardData()

        videos = course.get("videos", [])
        total_v = len(videos)
        completed_v = sum(1 for v in videos if v.get("completed", False))
        total_h = course.get("total_duration", 0) / 3600.0
        watched_h = sum(v.get("watched_duration", 0) for v in videos) / 3600.0
        today_s = self.get_today_progress(course_id)
        plan_s = self.get_today_plan_seconds(course_id)
        bal_min, _, _ = self.get_course_balance(course_id)

        return DashboardData(
            total_videos=total_v,
            completed_videos=completed_v,
            total_hours=total_h,
            watched_hours=watched_h,
            today_hours=today_s / 3600.0,
            plan_today_hours=plan_s / 3600.0,
            balance_hours=bal_min / 60.0,
            estimated_finish_str=self.estimate_finish_date(course_id),
            start_date_iso=course.get("start_date", ""),
            weekly_schedule=list(course.get("weekly_schedule", [0.0] * 7)),
            daily_stats=dict(course.get("daily_stats", {})),
        )

    # ==================== 活动日志 ====================

    def get_activity_log(self) -> dict:
        """获取活动日志"""
        return self.data.get("activity_log", {})

    def _calculate_streak(self) -> int:
        """计算当前连续学习天数"""
        log = self.data.get("activity_log", {})
        if not log:
            return 0

        today = date.today()
        streak = 0
        check_date = today

        # 检查今天是否有活动（有则从今天开始算，没有则从昨天开始）
        today_str = today.strftime("%Y-%m-%d")
        if today_str not in log:
            check_date = today - timedelta(days=1)

        while True:
            date_str = check_date.strftime("%Y-%m-%d")
            if date_str in log and log[date_str] > 0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return streak

    # ==================== 全局设置 ====================

    def get_setting(self, key: str, default=None):
        """获取全局设置"""
        settings = self.data.get("settings", {})
        return settings.get(key, default)

    def set_setting(self, key: str, value):
        """设置全局配置"""
        if "settings" not in self.data:
            self.data["settings"] = {}
        self.data["settings"][key] = value
        self._save_data()
