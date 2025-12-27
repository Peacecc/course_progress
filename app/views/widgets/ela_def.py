from enum import Enum, auto

class ElaThemeType:
    """
    Python implementation of ElaThemeType namespace.
    Contains ThemeMode and ThemeColor Enums.
    """
    class ThemeMode(Enum):
        Light = 0
        Dark = 1

    class ThemeColor(Enum):
        ScrollBarHandle = auto()
        ToggleSwitchNoToggledCenter = auto()
        WindowBase = auto()
        WindowCentralStackBase = auto()
        PrimaryNormal = auto()
        PrimaryHover = auto()
        PrimaryPress = auto()
        PopupBorder = auto()
        PopupBorderHover = auto()
        PopupBase = auto()
        PopupHover = auto()
        DialogBase = auto()
        DialogLayoutArea = auto()
        BasicText = auto()
        BasicTextInvert = auto()
        BasicDetailsText = auto()
        BasicTextNoFocus = auto()
        BasicTextDisable = auto()
        BasicTextPress = auto()
        BasicBorder = auto()
        BasicBorderDeep = auto()
        BasicBorderHover = auto()
        BasicBase = auto()
        BasicBaseDeep = auto()
        BasicDisable = auto()
        BasicHover = auto()
        BasicPress = auto()
        BasicSelectedHover = auto()
        BasicBaseLine = auto()
        BasicHemline = auto()
        BasicIndicator = auto()
        BasicChute = auto()
        BasicAlternating = auto()
        BasicBaseAlpha = auto()
        BasicBaseDeepAlpha = auto()
        BasicHoverAlpha = auto()
        BasicPressAlpha = auto()
        BasicSelectedAlpha = auto()
        BasicSelectedHoverAlpha = auto()
        StatusDanger = auto()
        Win10BorderActive = auto()
        Win10BorderInactive = auto()

class ElaIconType(Enum):
    """
    Subset of ElaIconType from C++ (FontAwesome mapping likely)
    """
    # Common Navigation / UI
    None_ = 0x0
    Broom = 0xf51a
    House = 0xee9a
    Gear = 0xf013
    User = 0xf007
    List = 0xf03a
    
    
    # Window Controls
    Dash = 0xebcf       # For minimize button
    Square = 0xf25e     # For maximize button  
    WindowMinimize = 0xf4be
    WindowMaximize = 0xf4bd
    WindowRestore = 0xf4bf
    Minimize = 0xf4be # window-minimize
    Maximize = 0xf4bd # window-maximize
    Restore = 0xf4bf  # window-restore
    Close = 0xf4ce    # xmark
    
    
    # Arrows
    ArrowLeft = 0xe86a   # Used for route back
    ArrowRight = 0xe86a  # Used for route forward
    Bars = 0xf20a        # Navigation menu icon
    AngleRight = 0xf105
    AngleDown = 0xf107
    AngleLeft = 0xf104
    AngleUp = 0xf106
    
    # Theme  
    MoonStars = 0xefed  # Theme toggle (dark mode)
    Moon = 0xefea
    Sun = 0xf2fe
    
    # Misc
    UpRightFromSquare = 0xf08e # external-link
    MagnifyingGlass = 0xf002
    Xmark = 0xf4ce


    # TODO: We need the actual Font file (ElaAwesome.ttf?) to map these correctly.
    # For now, we rely on the user having the font or we migrate the font file too.
    
class ElaTextType(Enum):
    NoStyle = 0x0000
    Caption = 0x0001
    Body = 0x0002
    BodyStrong = 0x0003
    Subtitle = 0x0004
    Title = 0x0005
    TitleLarge = 0x0006
    Display = 0x0007
