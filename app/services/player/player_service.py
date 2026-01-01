import os

def _add_vlc_to_path():
    import sys
    if sys.platform != 'win32': return True
    
    # 1. 尝试从注册表查找
    try:
        import winreg
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                key = winreg.OpenKey(root, r"SOFTWARE\VideoLAN\VLC")
                install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                dll_path = os.path.join(install_dir, "libvlc.dll")
                if os.path.exists(dll_path):
                    os.add_dll_directory(install_dir)
                    os.environ["PATH"] = install_dir + os.pathsep + os.environ["PATH"]
                    return True
            except (FileNotFoundError, Exception):
                continue
    except Exception:
        pass

    # 2. 搜索常见路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    vlc_paths = [
        project_root,
        r"C:\Program Files\VideoLAN\VLC", 
        r"C:\Program Files (x86)\VideoLAN\VLC",
        r"D:\Program\VLC",
        r"D:\Program Files\VideoLAN\VLC",
        r"D:\Program Files (x86)\VideoLAN\VLC"
    ]
    
    for p in vlc_paths:
        dll_path = os.path.join(p, "libvlc.dll")
        if os.path.exists(dll_path):
            try:
                os.add_dll_directory(p)
            except Exception:
                pass
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
            return True
    return False

VLC_AVAILABLE = _add_vlc_to_path()
try:
    import vlc
except ImportError:
    VLC_AVAILABLE = False

if VLC_AVAILABLE:
    print(f"[PlayerService] VLC Backend is AVAILABLE (libvlc version: {vlc.libvlc_get_version()})")
else:
    print("[PlayerService] VLC Backend is NOT available, falling back to Qt")

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
    def set_volume(self, volume): raise NotImplementedError

class VLCPlayerProxy(PlayerInterface):
    def __init__(self, hwnd=None):
        # 尝试使用单字符串传递参数，某些场景下比列表更稳定
        # --audio-time-stretch: 变速不变调的核心参数
        # --audio-filter=scaletempo: 显式指定变速滤镜
        print("[VLCPlayerProxy] Initializing with audio-time-stretch")
        self.instance = vlc.Instance("--audio-time-stretch --audio-filter=scaletempo")
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
    def set_volume(self, volume): self.player.audio_set_volume(int(volume))

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

class QtPlayerProxy(PlayerInterface):
    def __init__(self, output_widget=None):
        print("[QtPlayerProxy] Initializing Qt Player")
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
    def set_volume(self, volume): self.audio_output.setVolume(volume / 100.0)
