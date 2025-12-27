from PySide6.QtCore import QObject
from models.data_manager import DataManager
from services.player.player_service import VLC_AVAILABLE, VLCPlayerProxy, QtPlayerProxy

class MainController(QObject):
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.view = None

    def set_view(self, view):
        self.view = view
        self._connect_signals()

    def _connect_signals(self):
        # 连接视图信号到控制器逻辑
        self.view.home_view.course_selected.connect(self.handle_course_selected)
        self.view.detail_view.back_requested.connect(self.handle_go_home)
        self.view.detail_view.progress_updated.connect(self.handle_progress_update)

    def handle_course_selected(self, course_id):
        course = self.data_manager.get_course_by_id(course_id)
        if course:
            self.view.detail_view.load_course(course)
            self.view.stack.setCurrentIndex(1)

    def handle_go_home(self):
        if hasattr(self.view.detail_view, 'player') and self.view.detail_view.player:
            self.view.detail_view.player.stop()
        self.view.home_view.refresh_list()
        self.view.stack.setCurrentIndex(0)

    def handle_progress_update(self, course_id, rel_path, watched, completed):
        self.data_manager.update_video_progress(course_id, rel_path, watched, completed)
        
    def get_player(self, video_surface_id=None, video_widget=None):
        if VLC_AVAILABLE and video_surface_id:
            return VLCPlayerProxy(video_surface_id)
        return QtPlayerProxy(video_widget)
