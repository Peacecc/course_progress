from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QFontDatabase
import os
from .ela_def import ElaThemeType

class ElaTheme(QObject):
    """
    Python Implementation of ElaTheme (Singleton).
    Manages Light/Dark mode and color palettes.
    """
    _instance = None
    theme_mode_changed = Signal(ElaThemeType.ThemeMode)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ElaTheme, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Prevent double init in Python singleton pattern
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__()
        self._initialized = True
        
        self._theme_mode = ElaThemeType.ThemeMode.Light
        
        self._light_theme_colors = {}
        self._dark_theme_colors = {}
        
        
        self._initFont()
        self._init_theme_colors()

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = ElaTheme()
        return cls._instance

    def set_theme_mode(self, mode: ElaThemeType.ThemeMode):
        if self._theme_mode != mode:
            self._theme_mode = mode
            self.theme_mode_changed.emit(mode)

    def get_theme_mode(self) -> ElaThemeType.ThemeMode:
        return self._theme_mode

    def get_theme_color(self, color_type: ElaThemeType.ThemeColor) -> QColor:
        if self._theme_mode == ElaThemeType.ThemeMode.Light:
            return self._light_theme_colors.get(color_type, QColor(255, 0, 0)) # Red fallback
        else:
            return self._dark_theme_colors.get(color_type, QColor(255, 0, 0))

    def _initFont(self):
        # Load ElaAwesome.ttf
        # Assuming font is at ui/ela_widgets/font/ElaAwesome.ttf
        # Get absolute path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, "font", "ElaAwesome.ttf")
        
        if os.path.exists(font_path):
             id = QFontDatabase.addApplicationFont(font_path)
             if id != -1:
                 print(f"Loaded font: {QFontDatabase.applicationFontFamilies(id)}")
             else:
                 print(f"Failed to load font from {font_path}")
        else:
             print(f"Font file not found: {font_path}")

    def _init_theme_colors(self):
        # --- Light Theme ---
        L = self._light_theme_colors
        ThemeColor = ElaThemeType.ThemeColor
        
        # Copied from ElaThemePrivate.cpp (Manual Port)
        L[ThemeColor.ScrollBarHandle] = QColor(0xA0, 0xA0, 0xA0)
        L[ThemeColor.ToggleSwitchNoToggledCenter] = QColor(0x5A, 0x5A, 0x5A)
        L[ThemeColor.PrimaryNormal] = QColor(0x00, 0x67, 0xC0)
        L[ThemeColor.PrimaryHover] = QColor(0x19, 0x75, 0xC5)
        L[ThemeColor.PrimaryPress] = QColor(0x31, 0x83, 0xCA)
        
        L[ThemeColor.WindowBase] = QColor(0xF3, 0xF3, 0xF3)
        L[ThemeColor.WindowCentralStackBase] = QColor(255, 255, 255, 80)
        
        L[ThemeColor.PopupBorder] = QColor(0xD6, 0xD6, 0xD6)
        L[ThemeColor.PopupBorderHover] = QColor(0xCC, 0xCC, 0xCC)
        L[ThemeColor.PopupBase] = QColor(0xFA, 0xFA, 0xFA)
        L[ThemeColor.PopupHover] = QColor(0xF0, 0xF0, 0xF0)
        
        L[ThemeColor.DialogBase] = QColor("#FFFFFF")
        L[ThemeColor.DialogLayoutArea] = QColor(0xF3, 0xF3, 0xF3)
        
        L[ThemeColor.BasicText] = QColor("#000000")
        L[ThemeColor.BasicTextInvert] = QColor("#FFFFFF")
        L[ThemeColor.BasicDetailsText] = QColor(0x87, 0x87, 0x87)
        L[ThemeColor.BasicTextNoFocus] = QColor(0x86, 0x86, 0x8A)
        L[ThemeColor.BasicTextDisable] = QColor(0xB6, 0xB6, 0xB6)
        L[ThemeColor.BasicTextPress] = QColor(0x5A, 0x5A, 0x5D)
        
        L[ThemeColor.BasicBorder] = QColor(0xE5, 0xE5, 0xE5)
        L[ThemeColor.BasicBorderDeep] = QColor(0xA8, 0xA8, 0xA8)
        L[ThemeColor.BasicBorderHover] = QColor(0xDA, 0xDA, 0xDA)
        L[ThemeColor.BasicBase] = QColor(0xFD, 0xFD, 0xFD)
        L[ThemeColor.BasicBaseDeep] = QColor(0xE6, 0xE6, 0xE6)
        L[ThemeColor.BasicDisable] = QColor(0xF5, 0xF5, 0xF5)
        L[ThemeColor.BasicHover] = QColor(0xF3, 0xF3, 0xF3)
        L[ThemeColor.BasicPress] = QColor(0xF7, 0xF7, 0xF7)
        L[ThemeColor.BasicSelectedHover] = QColor(0xEB, 0xEB, 0xEB)
        L[ThemeColor.BasicBaseLine] = QColor(0xD1, 0xD1, 0xD1)
        L[ThemeColor.BasicHemline] = QColor(0x86, 0x86, 0x86)
        L[ThemeColor.BasicIndicator] = QColor(0x75, 0x7C, 0x87)
        L[ThemeColor.BasicChute] = QColor(0xB3, 0xB3, 0xB3)
        
        L[ThemeColor.BasicAlternating] = QColor(0xEF, 0xEF, 0xEF, 160)
        L[ThemeColor.BasicBaseAlpha] = QColor(0xFF, 0xFF, 0xFF, 160)
        L[ThemeColor.BasicBaseDeepAlpha] = QColor(0xCC, 0xCC, 0xCC, 160)
        L[ThemeColor.BasicHoverAlpha] = QColor(0xCC, 0xCC, 0xCC, 70)
        L[ThemeColor.BasicPressAlpha] = QColor(0xCC, 0xCC, 0xCC, 40)
        L[ThemeColor.BasicSelectedAlpha] = QColor(0xCC, 0xCC, 0xCC, 70)
        L[ThemeColor.BasicSelectedHoverAlpha] = QColor(0xCC, 0xCC, 0xCC, 40)
        
        L[ThemeColor.StatusDanger] = QColor(0xE8, 0x11, 0x23)
        L[ThemeColor.Win10BorderActive] = QColor(0x6E, 0x6E, 0x6E)
        L[ThemeColor.Win10BorderInactive] = QColor(0xA7, 0xA7, 0xA7)


        # --- Dark Theme ---
        D = self._dark_theme_colors
        
        D[ThemeColor.ScrollBarHandle] = QColor(0x9F, 0x9F, 0x9F)
        D[ThemeColor.ToggleSwitchNoToggledCenter] = QColor(0xD0, 0xD0, 0xD0)
        D[ThemeColor.PrimaryNormal] = QColor(0x4C, 0xC2, 0xFF)
        D[ThemeColor.PrimaryHover] = QColor(0x47, 0xB1, 0xE8)
        D[ThemeColor.PrimaryPress] = QColor(0x42, 0xA1, 0xD2)
        
        D[ThemeColor.WindowBase] = QColor(0x20, 0x20, 0x20)
        D[ThemeColor.WindowCentralStackBase] = QColor(0x3E, 0x3E, 0x3E, 60)
        
        D[ThemeColor.PopupBorder] = QColor(0x47, 0x47, 0x47)
        D[ThemeColor.PopupBorderHover] = QColor(0x54, 0x54, 0x54)
        D[ThemeColor.PopupBase] = QColor(0x2C, 0x2C, 0x2C)
        D[ThemeColor.PopupHover] = QColor(0x38, 0x38, 0x38)
        
        D[ThemeColor.DialogBase] = QColor(0x1F, 0x1F, 0x1F)
        D[ThemeColor.DialogLayoutArea] = QColor(0x20, 0x20, 0x20)
        
        D[ThemeColor.BasicText] = QColor("#FFFFFF")
        D[ThemeColor.BasicTextInvert] = QColor("#000000")
        D[ThemeColor.BasicDetailsText] = QColor(0xAD, 0xAD, 0xB0)
        D[ThemeColor.BasicTextNoFocus] = QColor(0x86, 0x86, 0x8A)
        D[ThemeColor.BasicTextDisable] = QColor(0xA7, 0xA7, 0xA7)
        D[ThemeColor.BasicTextPress] = QColor(0xBB, 0xBB, 0xBF)
        
        D[ThemeColor.BasicBorder] = QColor(0x4B, 0x4B, 0x4B)
        D[ThemeColor.BasicBorderDeep] = QColor(0x5C, 0x5C, 0x5C)
        D[ThemeColor.BasicBorderHover] = QColor(0x57, 0x57, 0x57)
        D[ThemeColor.BasicBase] = QColor(0x34, 0x34, 0x34)
        D[ThemeColor.BasicBaseDeep] = QColor(0x61, 0x61, 0x61)
        D[ThemeColor.BasicDisable] = QColor(0x2A, 0x2A, 0x2A)
        D[ThemeColor.BasicHover] = QColor(0x40, 0x40, 0x40)
        D[ThemeColor.BasicPress] = QColor(0x3A, 0x3A, 0x3A)
        D[ThemeColor.BasicSelectedHover] = QColor(0x38, 0x38, 0x38)
        D[ThemeColor.BasicBaseLine] = QColor(0x45, 0x45, 0x45)
        D[ThemeColor.BasicHemline] = QColor(0x9A, 0x9A, 0x9A)
        D[ThemeColor.BasicIndicator] = QColor(0x75, 0x7C, 0x87)
        D[ThemeColor.BasicChute] = QColor(0x63, 0x63, 0x63)
        
        D[ThemeColor.BasicAlternating] = QColor(0x45, 0x45, 0x45, 125)
        D[ThemeColor.BasicBaseAlpha] = QColor(0x2D, 0x2D, 0x2D, 95)
        D[ThemeColor.BasicBaseDeepAlpha] = QColor(0x72, 0x72, 0x72, 95)
        D[ThemeColor.BasicHoverAlpha] = QColor(0x4B, 0x4B, 0x4B, 75)
        D[ThemeColor.BasicPressAlpha] = QColor(0x4B, 0x4B, 0x4B, 55)
        D[ThemeColor.BasicSelectedAlpha] = QColor(0x4B, 0x4B, 0x4B, 75)
        D[ThemeColor.BasicSelectedHoverAlpha] = QColor(0x4B, 0x4B, 0x4B, 55)
        
        D[ThemeColor.StatusDanger] = QColor(0xE8, 0x11, 0x23)
        D[ThemeColor.Win10BorderActive] = QColor(0x33, 0x33, 0x33)
        D[ThemeColor.Win10BorderInactive] = QColor(0x3D, 0x3D, 0x3D)

ela_theme = ElaTheme()
