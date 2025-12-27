import os

def _add_vlc_to_path():
    import sys
    if sys.platform != 'win32': return True
    
    # 搜索路径：项目根目录（当前 libvlc.dll 所在处）以及标准安装路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    vlc_paths = [
        project_root,
        r"C:\Program Files\VideoLAN\VLC", 
        r"C:\Program Files (x86)\VideoLAN\VLC"
    ]
    
    found = False
    for p in vlc_paths:
        dll_path = os.path.join(p, "libvlc.dll")
        if os.path.exists(dll_path):
            try:
                # Python 3.8+ 必须使用 add_dll_directory
                os.add_dll_directory(p)
            except (AttributeError, Exception):
                pass
            # 同时更新 PATH 环境变量
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
            found = True
            # 不直接返回，可能需要添加多个路径依赖（虽然通常一个就够）
    return found

VLC_AVAILABLE = _add_vlc_to_path()
try:
    import vlc
except ImportError:
    VLC_AVAILABLE = False

class PlayerInterface:
    def set_media(self, path): raise NotImplementedError
    def play(self): raise NotImplementedError
    def pause(self): raise NotImplementedError
    def stop(self): raise NotImplementedError
    def set_rate(self, rate): raise NotImplementedError
    def get_time(self): raise NotImplementedError
    def set_time(self, ms): raise NotImplementedError
    def get_length(self): raise NotImplementedError
    def is_playing(self): raise NotImplementedError

class VLCPlayerProxy(PlayerInterface):
    def __init__(self, hwnd=None):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        if hwnd: self.player.set_hwnd(hwnd)
    def set_media(self, path):
        media = self.instance.media_new(os.path.abspath(path))
        self.player.set_media(media)
    def play(self): self.player.play()
    def pause(self): self.player.pause()
    def stop(self): self.player.stop()
    def set_rate(self, rate): self.player.set_rate(rate)
    def get_time(self): return self.player.get_time()
    def set_time(self, ms): self.player.set_time(int(ms))
    def get_length(self): return self.player.get_length()
    def is_playing(self): return self.player.is_playing()

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

class QtPlayerProxy(PlayerInterface):
    def __init__(self, output_widget=None):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        if output_widget: self.player.setVideoOutput(output_widget)
    def set_media(self, path): self.player.setSource(QUrl.fromLocalFile(path))
    def play(self): self.player.play()
    def pause(self): self.player.pause()
    def stop(self): self.player.stop()
    def set_rate(self, rate): self.player.setPlaybackRate(rate)
    def get_time(self): return self.player.position()
    def set_time(self, ms): self.player.setPosition(int(ms))
    def get_length(self): return self.player.duration()
    def is_playing(self): return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
