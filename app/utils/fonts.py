"""字体管理模块 — 统一加载和配置应用字体（阿里巴巴普惠体 3.0）

使用方法：
1. 从 https://fonts.alibabagroup.com/ 下载阿里巴巴普惠体 3.0
2. 将以下文件放入 app/assets/fonts/:
   - AlibabaPuHuiTi-3-55-Regular.ttf (或 .otf)
   - AlibabaPuHuiTi-3-65-Medium.ttf  (或 .otf)
   - AlibabaPuHuiTi-3-85-Bold.ttf     (或 .otf)
3. 重新启动应用

如果字体文件不存在，会自动降级为系统字体（Microsoft YaHei）。
"""

import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication


_ASSETS_FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

_FONT_CANDIDATES = [
    # (weight_key, [可能的文件名列表])
    ("Regular", [
        "AlibabaPuHuiTi-3-55-Regular.ttf",
        "AlibabaPuHuiTi-3-55-Regular.otf",
        "AlibabaPuHuiTi-3-55-Regular L3.ttf",
    ]),
    ("Medium", [
        "AlibabaPuHuiTi-3-65-Medium.ttf",
        "AlibabaPuHuiTi-3-65-Medium.otf",
    ]),
    ("Bold", [
        "AlibabaPuHuiTi-3-85-Bold.ttf",
        "AlibabaPuHuiTi-3-85-Bold.otf",
    ]),
]

_loaded: dict[str, str] = {}
_available = False


def load_fonts() -> bool:
    """加载字体，成功返回 True"""
    global _available, _loaded

    # 1. 尝试加载内置字体
    for weight, filenames in _FONT_CANDIDATES:
        for fname in filenames:
            font_path = _ASSETS_FONTS_DIR / fname
            if font_path.exists():
                try:
                    fid = QFontDatabase.addApplicationFont(str(font_path))
                    if fid >= 0:
                        families = QFontDatabase.applicationFontFamilies(fid)
                        if families:
                            _loaded[weight] = families[0]
                            print(f"[Fonts] {families[0]} ({weight})")
                            break
                except Exception as e:
                    print(f"[Fonts] {fname}: {e}")

    # 2. 检查系统字体
    if not _loaded:
        sys_family = _find_system_font()
        if sys_family:
            for w in ["Regular", "Medium", "Bold"]:
                _loaded[w] = sys_family

    _available = bool(_loaded)
    if _available:
        print(f"[Fonts] 使用字体: {_loaded.get('Regular', 'unknown')}")
    else:
        print("[Fonts] 未找到阿里巴巴普惠体，使用系统默认字体")
    return _available


def _find_system_font() -> str | None:
    """在系统字体中查找阿里巴巴普惠体"""
    try:
        if sys.platform == "win32":
            import winreg
            for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    key = winreg.OpenKey(root,
                        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
                    i = 0
                    while True:
                        try:
                            name, data, _ = winreg.EnumValue(key, i)
                            if "Alibaba PuHuiTi" in name or "阿里巴巴普惠体" in name:
                                family = name.split("(")[0].strip().rstrip(" 常规")
                                if family:
                                    winreg.CloseKey(key)
                                    return family
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except OSError:
                    continue
    except Exception:
        pass
    return None


def is_available() -> bool:
    return _available


def get_font(weight: str = "Regular", size: int = 12) -> QFont:
    """获取指定字重和大小的 QFont"""
    family = _loaded.get(weight) or _loaded.get("Regular")

    if not family:
        family = "Microsoft YaHei" if sys.platform == "win32" else "sans-serif"

    font = QFont(family, size)
    weight_map = {
        "Regular": QFont.Weight.Normal,
        "Medium": QFont.Weight.Medium,
        "Bold": QFont.Weight.Bold,
    }
    font.setWeight(weight_map.get(weight, QFont.Weight.Normal))
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return font


def apply_global_font(app: QApplication):
    """设置应用全局默认字体"""
    family = _loaded.get("Regular", "Microsoft YaHei")
    font = QFont(family, 10)
    app.setFont(font)
    print(f"[Fonts] 全局字体: {family}")
