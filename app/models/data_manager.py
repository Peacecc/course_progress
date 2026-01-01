import json
import uuid
from datetime import datetime
from utils.paths import PathManager

class DataManager:
    """数据管理器，负责课程数据的加载、保存和操作"""
    
    def __init__(self, data_file=PathManager.COURSES_JSON):
        """
        初始化数据管理器
        
        Args:
            data_file: 数据文件路径，默认为COURSES_JSON
        """
        self.data_file = data_file
        # 确保所需目录存在
        PathManager.ensure_dirs()
        # 加载数据
        self.data = self._load_data()

    def _load_data(self):
        """
        从JSON文件加载数据
        
        Returns:
            加载的数据字典，如果文件不存在或格式错误则返回默认结构
        """
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # 文件不存在或JSON格式错误时返回默认数据结构
            return {"courses": []}

    def _save_data(self, data=None):
        """
        保存数据到JSON文件
        
        Args:
            data: 要保存的数据，如果为None则保存当前数据
        """
        if data is None:
            data = self.data
        with open(self.data_file, 'w', encoding='utf-8') as f:
            # 格式化保存JSON，确保中文正常显示
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_course(self, name, path, videos_data, duration_stats):
        """
        添加新课程
        
        Args:
            name: 课程名称
            path: 课程路径
            videos_data: 视频数据列表
            duration_stats: 时长统计信息
            
        Returns:
            新创建的课程数据字典
        """
        # 生成唯一课程ID
        course_id = str(uuid.uuid4())
        
        # 构建课程数据结构
        new_course = {
            "id": course_id,
            "name": name,  # 课程名称
            "path": path,  # 课程路径
            "added_at": datetime.now().isoformat(),  # 添加时间
            "total_videos": duration_stats['total_videos'],  # 总视频数
            "total_duration": duration_stats['total_duration'],  # 总时长
            "videos": [],  # 视频列表
            "daily_limit_date": None  # 每日限制日期
        }
        
        # 添加视频数据
        for v in videos_data:
            new_course["videos"].append({
                "rel_path": v['rel_path'],  # 相对路径
                "duration": v['duration'],  # 视频总时长
                "watched_duration": 0,  # 已观看时长
                "completed": False,  # 是否完成观看
                "last_watched": None  # 最后观看时间
            })
        
        # 添加到数据中并保存
        self.data["courses"].append(new_course)
        self._save_data()
        return new_course

    def get_courses(self):
        """
        获取所有课程列表
        
        Returns:
            课程列表
        """
        return self.data.get("courses", [])
        
    def get_course_by_id(self, course_id):
        """
        根据ID获取课程
        
        Args:
            course_id: 课程ID
            
        Returns:
            课程数据字典，如果未找到则返回None
        """
        for course in self.data.get("courses", []):
            if course["id"] == course_id:
                return course
        return None

    def update_video_progress(self, course_id, rel_path, watched_duration, completed):
        """
        更新视频观看进度
        
        Args:
            course_id: 课程ID
            rel_path: 视频相对路径
            watched_duration: 已观看时长
            completed: 是否已完成观看
        """
        # 查找课程
        course = self.get_course_by_id(course_id)
        if not course: 
            return
        
        # 处理每日统计
        today_str = datetime.now().strftime("%Y-%m-%d")
        if "daily_stats" not in course: 
            course["daily_stats"] = {}
        if today_str not in course["daily_stats"]: 
            course["daily_stats"][today_str] = 0
            
        # 更新指定视频的进度
        for video in course["videos"]:
            if video["rel_path"] == rel_path:
                # 计算新增的观看时长
                prev_watched = video.get("watched_duration", 0)
                if watched_duration > prev_watched:
                    delta = watched_duration - prev_watched
                    course["daily_stats"][today_str] += delta
                    video["watched_duration"] = watched_duration
                
                # 标记为完成（如果完成）
                if completed and not video.get("completed", False):
                    video["completed"] = True
                    self.log_activity()  # 记录完成活动
                    
                # 更新最后观看时间
                video["last_watched"] = datetime.now().isoformat()
                break
                
        # 保存更新后的数据
        self._save_data()

    def log_activity(self):
        """记录活动日志（视频完成记录）"""
        today = datetime.now().strftime("%Y-%m-%d")
        log = self.data.get("activity_log", {})
        # 今日完成数+1
        log[today] = log.get(today, 0) + 1
        self.data["activity_log"] = log
        self._save_data()

    def delete_course(self, course_id):
        """
        删除课程
        
        Args:
            course_id: 要删除的课程ID
        """
        # 过滤掉指定ID的课程
        self.data["courses"] = [c for c in self.data["courses"] if c["id"] != course_id]
        self._save_data()

    def get_activity_log(self):
        """
        获取活动日志
        
        Returns:
            按日期分组的活动日志字典
        """
        return self.data.get("activity_log", {})