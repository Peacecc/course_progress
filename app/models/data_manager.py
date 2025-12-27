import json
import uuid
from datetime import datetime
from utils.paths import PathManager

class DataManager:
    def __init__(self, data_file=PathManager.COURSES_JSON):
        self.data_file = data_file
        PathManager.ensure_dirs()
        self.data = self._load_data()

    def _load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"courses": []}

    def _save_data(self, data=None):
        if data is None:
            data = self.data
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_course(self, name, path, videos_data, duration_stats):
        course_id = str(uuid.uuid4())
        new_course = {
            "id": course_id,
            "name": name,
            "path": path,
            "added_at": datetime.now().isoformat(),
            "total_videos": duration_stats['total_videos'],
            "total_duration": duration_stats['total_duration'],
            "videos": [],
            "daily_limit_date": None
        }
        for v in videos_data:
            new_course["videos"].append({
                "rel_path": v['rel_path'],
                "duration": v['duration'],
                "watched_duration": 0,
                "completed": False,
                "last_watched": None
            })
        self.data["courses"].append(new_course)
        self._save_data()
        return new_course

    def get_courses(self):
        return self.data.get("courses", [])
        
    def get_course_by_id(self, course_id):
        for course in self.data.get("courses", []):
            if course["id"] == course_id:
                return course
        return None

    def update_video_progress(self, course_id, rel_path, watched_duration, completed):
        course = self.get_course_by_id(course_id)
        if not course: return
            
        today_str = datetime.now().strftime("%Y-%m-%d")
        if "daily_stats" not in course: course["daily_stats"] = {}
        if today_str not in course["daily_stats"]: course["daily_stats"][today_str] = 0
            
        for video in course["videos"]:
            if video["rel_path"] == rel_path:
                prev_watched = video.get("watched_duration", 0)
                if watched_duration > prev_watched:
                    delta = watched_duration - prev_watched
                    course["daily_stats"][today_str] += delta
                    video["watched_duration"] = watched_duration
                
                if completed and not video.get("completed", False):
                    video["completed"] = True
                    self.log_activity()
                video["last_watched"] = datetime.now().isoformat()
                break
        self._save_data()

    def log_activity(self):
        today = datetime.now().strftime("%Y-%m-%d")
        log = self.data.get("activity_log", {})
        log[today] = log.get(today, 0) + 1
        self.data["activity_log"] = log
        self._save_data()

    def delete_course(self, course_id):
        self.data["courses"] = [c for c in self.data["courses"] if c["id"] != course_id]
        self._save_data()

    def get_activity_log(self):
        return self.data.get("activity_log", {})
