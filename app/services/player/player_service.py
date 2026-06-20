"""播放器服务 — VLC 主引擎 + Qt Multimedia 备用引擎，统一 PlayerInterface 抽象"""

import os
import sys
import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

from utils.paths import PathManager
from utils.logger import setup_logger

logger = setup_logger("PlayerService", PathManager.LOG_DIR)

# ==================== VLC 路径探测 ====================

VLC_PATH_CANDIDATES = [
    # 常见安装路径
    r"C:\Program Files\VideoLAN\VLC",
    r"C:\Program Files (x86)\VideoLAN\VLC",
    r"D:\Program Files\VideoLAN\VLC",
    r"D:\Program Files (x86)\VideoLAN\VLC",
    r"E:\Program Files\VideoLAN\VLC",
]


def _find_vlc_dll() -> str | None:
    """探测 VLC 安装目录并返回包含 libvlc.dll 的路径"""
    if sys.platform != "win32":
        return None

    # 方法 1：注册表
    try:
        import winreg
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                key = winreg.OpenKey(root, r"SOFTWARE\VideoLAN\VLC")
                install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                dll_path = os.path.join(install_dir, "libvlc.dll")
                if os.path.exists(dll_path):
                    logger.info(f"VLC 通过注册表找到: {install_dir}")
                    return install_dir
            except (FileNotFoundError, OSError):
                continue
    except Exception:
        pass

    # 方法 2：常见路径
    for p in VLC_PATH_CANDIDATES:
        dll_path = os.path.join(p, "libvlc.dll")
        if os.path.exists(dll_path):
            logger.info(f"VLC 通过路径扫描找到: {p}")
            return p

    # 方法 3：PATH 环境变量
    for p in os.environ.get("PATH", "").split(os.pathsep):
        dll_path = os.path.join(p, "libvlc.dll")
        if os.path.exists(dll_path):
            logger.info(f"VLC 通过 PATH 找到: {p}")
            return p

    return None


def _add_vlc_to_path() -> bool:
    """将 VLC 目录添加到 DLL 搜索路径，成功返回 True"""
    vlc_dir = _find_vlc_dll()
    if not vlc_dir:
        logger.warning("VLC 未找到 — 将使用 Qt Multimedia 引擎")
        return False

    try:
        os.add_dll_directory(vlc_dir)
    except Exception:
        pass
    os.environ["PATH"] = vlc_dir + os.pathsep + os.environ.get("PATH", "")
    return True


VLC_AVAILABLE = _add_vlc_to_path()

try:
    import vlc
    _vlc_version = vlc.libvlc_get_version().decode() if hasattr(vlc, 'libvlc_get_version') else "unknown"
    logger.info(f"python-vlc 已加载 (libvlc {_vlc_version})")
except ImportError:
    VLC_AVAILABLE = False
    logger.warning("python-vlc 未安装 — 将使用 Qt Multimedia 引擎")


# ==================== 播放器接口 ====================

class PlayerInterface:
    """播放器抽象接口"""

    def set_media(self, path: str): raise NotImplementedError
    def play(self): raise NotImplementedError
    def pause(self): raise NotImplementedError
    def stop(self): raise NotImplementedError
    def set_rate(self, rate: float): raise NotImplementedError
    def get_time(self) -> int: raise NotImplementedError
    def set_time(self, ms: int): raise NotImplementedError
    def get_length(self) -> int: raise NotImplementedError
    def is_playing(self) -> bool: raise NotImplementedError
    def set_volume(self, volume: int): raise NotImplementedError
    def release(self): pass  # 清理资源（可选）


# ==================== VLC 实现 ====================

class VLCPlayerProxy(PlayerInterface):
    """VLC 播放器代理"""

    def __init__(self, hwnd: int = None):
        logger.info("VLCPlayerProxy 初始化 (audio-time-stretch 模式)")
        self.instance = vlc.Instance("--audio-time-stretch --audio-filter=scaletempo")
        self.player = self.instance.media_player_new()
        if hwnd:
            self.player.set_hwnd(hwnd)
        self._current_media = None

    def set_media(self, path: str):
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            logger.warning(f"视频文件不存在: {abs_path}")
            return
        self._current_media = self.instance.media_new(abs_path)
        self.player.set_media(self._current_media)

    def play(self): self.player.play()
    def pause(self): self.player.pause()
    def stop(self): self.player.stop()

    def set_rate(self, rate: float):
        self.player.set_rate(rate)

    def get_time(self) -> int: return self.player.get_time()
    def set_time(self, ms: int): self.player.set_time(int(ms))
    def get_length(self) -> int: return self.player.get_length()
    def is_playing(self) -> bool: return bool(self.player.is_playing())
    def set_volume(self, volume: int): self.player.audio_set_volume(int(volume))

    def release(self):
        if self.player:
            self.player.stop()
            self.player.release()
        if self.instance:
            self.instance.release()


# ==================== Qt Multimedia 实现 ====================

class QtPlayerProxy(PlayerInterface):
    """Qt Multimedia 播放器代理（VLC 不可用时的后备方案）"""

    def __init__(self, output_widget=None):
        logger.info("QtPlayerProxy 初始化")
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        if output_widget:
            self.player.setVideoOutput(output_widget)

    def set_media(self, path: str):
        url = QUrl.fromLocalFile(os.path.abspath(path))
        self.player.setSource(url)

    def play(self): self.player.play()
    def pause(self): self.player.pause()
    def stop(self): self.player.stop()

    def set_rate(self, rate: float):
        self.player.setPlaybackRate(rate)

    def get_time(self) -> int: return self.player.position()
    def set_time(self, ms: int): self.player.setPosition(int(ms))
    def get_length(self) -> int: return self.player.duration()

    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def set_volume(self, volume: int):
        self.audio_output.setVolume(max(0.0, min(1.0, volume / 100.0)))

    def release(self):
        if self.player:
            self.player.stop()
