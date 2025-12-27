from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Qt, QSize, QRectF, QPointF, Property, QUrl
from PySide6.QtGui import QPainter, QPainterPath, QColor, QFont, QPixmap, QDesktopServices, QPen, QBrush

import os
from .ela_theme import ela_theme
from .ela_def import ElaThemeType, ElaIconType

class ElaCardPixMode:
    Ellipse = 0
    Default = 1
    RoundedRect = 2

class ElaAcrylicUrlCard(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 200)
        
        self._border_radius = 5
        self._main_opacity = 0.95
        self._noise_opacity = 0.06
        self._brush_alpha = 245
        
        self._title = ""
        self._sub_title = ""
        self._title_pixel_size = 15
        self._sub_title_pixel_size = 12
        self._title_spacing = 10
        self._sub_title_spacing = 10
        
        self._card_pixmap = QPixmap()
        self._card_pixmap_size = QSize(54, 54)
        self._card_pixmap_border_radius = 6
        self._card_pix_mode = ElaCardPixMode.Ellipse
        
        self._url = ""
        
        self._theme_mode = ela_theme.get_theme_mode()
        ela_theme.theme_mode_changed.connect(self._on_theme_changed)
        
        # Load Noise Image
        noise_path = os.path.join(os.path.dirname(__file__), "image", "noise.png")
        self._noise_pix = QPixmap(noise_path) if os.path.exists(noise_path) else QPixmap()

        self.clicked.connect(self._on_clicked)

    def _on_theme_changed(self, mode):
        self._theme_mode = mode
        self.update()

    def _on_clicked(self):
        if self._url:
            QDesktopServices.openUrl(QUrl(self._url))

    def set_title(self, title):
        self._title = title
        self.update()

    def set_sub_title(self, sub_title):
        self._sub_title = sub_title
        self.update()

    def set_url(self, url):
        self._url = url

    def set_card_pixmap(self, pixmap):
        self._card_pixmap = pixmap
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.SmoothPixmapTransform | QPainter.Antialiasing | QPainter.TextAntialiasing)
        
        painter.save()
        
        # Draw Background (Acrylic Style)
        border_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicBorderHover) if self.underMouse() else ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicBorder)
        painter.setPen(QPen(border_color, 1))
        
        brush_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicHover) if self.underMouse() else ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicBase)
        brush_color.setAlpha(self._brush_alpha)
        painter.setBrush(brush_color)
        
        rect = self.rect()
        rect.adjust(1, 1, -1, -1)
        
        # Draw Noise
        if not self._noise_pix.isNull():
            painter.setOpacity(self._noise_opacity)
            painter.drawPixmap(rect, self._noise_pix)
            
        painter.setOpacity(self._main_opacity)
        painter.drawRoundedRect(rect, self._border_radius, self._border_radius)
        
        painter.restore()
        
        # Draw Pixmap
        pix_rect = QRectF(self.width() / 8.5, self.height() / 4 - self._card_pixmap_size.height() / 2, 
                          self._card_pixmap_size.width(), self._card_pixmap_size.height())
                          
        if not self._card_pixmap.isNull():
            painter.save()
            path = QPainterPath()
            if self._card_pix_mode == ElaCardPixMode.Ellipse:
                path.addEllipse(pix_rect.center(), self._card_pixmap_size.width() / 2, self._card_pixmap_size.height() / 2)
                painter.setClipPath(path)
                painter.drawPixmap(pix_rect.toRect(), self._card_pixmap)
            # Handle other modes if needed
            painter.restore()
            
        # Draw Text
        painter.save()
        font = self.font()
        font.setBold(True)
        font.setPixelSize(self._title_pixel_size)
        painter.setFont(font)
        painter.setPen(ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicText))
        
        title_rect = QRectF(pix_rect.x(), pix_rect.bottom() + self._title_spacing, 
                            self.width() - self.width() / 7, self.height() / 3)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextSingleLine, self._title)
        
        font.setBold(False)
        font.setPixelSize(self._sub_title_pixel_size)
        painter.setFont(font)
        painter.setPen(ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicDetailsText))
        
        fm = painter.fontMetrics()
        title_height = fm.boundingRect(self._title).height() * 1.1 
        # C++ logic implies checking actual rendered height of title if wrapped? 
        # But here title is SingleLine.
        
        sub_title_rect = QRectF(pix_rect.x(), pix_rect.bottom() + self._title_spacing + title_height + self._sub_title_spacing, 
                                self.width() - self.width() / 7, self.height() / 3)
        painter.drawText(sub_title_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self._sub_title)
        
        painter.restore()
        
        # Draw Icon (Link Arrow)
        painter.save()
        icon_font = QFont("ElaAwesome")
        icon_font.setPixelSize(13)
        painter.setFont(icon_font)
        painter.setPen(ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicText))
        # 0xf08e is 'up-right-from-square' in FA 6, check specific char
        # Assuming we need to map ElaIconType::UpRightFromSquare -> char
        # For now, using a placeholder char or verifying mapping.
        # C++ uses: QChar((unsigned short)ElaIconType::UpRightFromSquare)
        painter.drawText(self.width() - 1.5 * 13, self.height() - 13, chr(ElaIconType.UpRightFromSquare.value))
        painter.restore()


class ElaInteractiveCard(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(270, 80)
        self.setMouseTracking(True)
        
        self._border_radius = 6
        self._title = ""
        self._sub_title = ""
        self._title_pixel_size = 15
        self._sub_title_pixel_size = 12
        self._title_spacing = 2
        
        self._card_pixmap = QPixmap()
        self._card_pixmap_size = QSize(64, 64)
        self._card_pix_mode = ElaCardPixMode.Ellipse
        
        self._theme_mode = ela_theme.get_theme_mode()
        ela_theme.theme_mode_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, mode):
        self._theme_mode = mode
        self.update()

    def set_title(self, title):
        self._title = title
        self.update()

    def set_sub_title(self, sub):
        self._sub_title = sub
        self.update()

    def set_card_pixmap(self, pix):
        self._card_pixmap = pix
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.SmoothPixmapTransform | QPainter.Antialiasing | QPainter.TextAntialiasing)
        painter.setPen(Qt.NoPen)
        
        # Hover Background
        if self.underMouse():
            brush_color = ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicHoverAlpha)
            painter.setBrush(brush_color)
            painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)
            
        # Image
        if not self._card_pixmap.isNull():
            painter.save()
            path = QPainterPath()
            if self._card_pix_mode == ElaCardPixMode.Ellipse:
                # Center Y
                cy = self.height() / 2
                offset_x = 10
                # Ellipse center
                center = QPointF(offset_x + self._card_pixmap_size.width() / 2, cy)
                
                path.addEllipse(center, self._card_pixmap_size.width() / 2, self._card_pixmap_size.height() / 2)
                painter.setClipPath(path)
                
                target_rect = QRectF(offset_x, cy - self._card_pixmap_size.height() / 2, 
                                     self._card_pixmap_size.width(), self._card_pixmap_size.height())
                painter.drawPixmap(target_rect.toRect(), self._card_pixmap)
            painter.restore()
            
        # Text
        painter.setPen(ela_theme.get_theme_color(ElaThemeType.ThemeColor.BasicText))
        font = self.font()
        font.setBold(True)
        font.setPixelSize(self._title_pixel_size)
        painter.setFont(font)
        
        text_start_x = self._card_pixmap_size.width() + 26
        text_width = self.width() - text_start_x
        
        title_rect = QRectF(text_start_x, 0, text_width, self.height() / 2 - self._title_spacing)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignBottom | Qt.TextWordWrap, self._title)
        
        font.setBold(False)
        font.setPixelSize(self._sub_title_pixel_size)
        painter.setFont(font)
        sub_rect = QRectF(text_start_x, self.height() / 2 + self._title_spacing, text_width, self.height() / 2)
        painter.drawText(sub_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self._sub_title)
