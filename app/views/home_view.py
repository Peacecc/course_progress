from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QScrollArea, QGridLayout, QLabel, QFileDialog, QMessageBox, QProgressDialog)
from PySide6.QtCore import Qt, Signal, QThread, QSize
from PySide6.QtGui import QCursor
from views.widgets.sdk_stubs import (ElaAcrylicUrlCard, ela_theme, ElaThemeType, HeatMapWidget, GoalCountdownWidget)
from services.theme_service import theme_service
from models.data_manager import DataManager
from services.scanner import VideoScanner
import os

class ScanThread(QThread):
    finished = Signal(str, str, list, dict)
    def __init__(self, path): super().__init__(); self.path = path
    def run(self):
        name = os.path.basename(self.path)
        videos, stats = VideoScanner.scan_directory(self.path)
        self.finished.emit(name, self.path, videos, stats)

class HomeView(QWidget):
    course_selected = Signal(str) 
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_manager = DataManager()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)
        
        # --- Top Dashboard Area ---
        dash_layout = QHBoxLayout()
        dash_layout.setSpacing(15)
        
        # Left: Countdown
        self.countdown_widget = GoalCountdownWidget()
        self.countdown_widget.setFixedWidth(320)
        dash_layout.addWidget(self.countdown_widget)
        
        # Right: HeatMap (fills rest)
        self.heatmap_widget = HeatMapWidget()
        dash_layout.addWidget(self.heatmap_widget)
        
        main_layout.addLayout(dash_layout)
        
        # --- Middle: Toolbar ---
        toolbar = QHBoxLayout()
        self.label_courses = QLabel("我的课程库")
        self.label_courses.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 10px;")
        toolbar.addWidget(self.label_courses)
        
        toolbar.addStretch()
        
        self.add_btn = QPushButton("+ 添加课程")
        self.add_btn.setFixedSize(120, 40)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_course)
        toolbar.addWidget(self.add_btn)
        
        main_layout.addLayout(toolbar)
        
        # --- Bottom: Grid ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")
        
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setSpacing(20)
        
        self.scroll_area.setWidget(self.grid_widget)
        main_layout.addWidget(self.scroll_area)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(1, 1)
        main_layout.setStretch(2, 9)
        
        theme_service.theme_changed.connect(lambda t: self.apply_theme(0 if t['name'] == 'light' else 1))
        self.apply_theme(1) # Default dark
        
        self.refresh_list()

    def apply_theme(self, mode):
        # Update label colors based on theme if needed
        is_light = (mode == ElaThemeType.ThemeMode.Light)
        text_color = "black" if is_light else "white"
        self.label_courses.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {text_color}; margin-top: 10px;")
        
        accent = "#0078D4" # Default Primary
        accent_hover = "#1084D9"
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent}; 
                color: white; 
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {accent_hover};
            }}
        """)

    def add_course(self):
        folder = QFileDialog.getExistingDirectory(self, "选择课程文件夹")
        if not folder: return
        courses = self.data_manager.get_courses()
        for course in courses:
            if course['path'] == folder:
                QMessageBox.warning(self, "提示", "该课程已添加到列表中")
                return

        self.progress_dialog = QProgressDialog("正在深入扫描课程视频...", "取消", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        self.scan_thread = ScanThread(folder)
        self.scan_thread.finished.connect(self.on_scan_finished)
        self.scan_thread.finished.connect(self.progress_dialog.close)
        self.scan_thread.start()

    def on_scan_finished(self, name, path, videos, stats):
        if stats['total_videos'] == 0:
            QMessageBox.warning(self, "提示", "未在该文件夹中找到视频文件")
            return
        self.data_manager.add_course(name, path, videos, stats)
        self.refresh_list()
        
    def refresh_list(self):
        for i in reversed(range(self.grid_layout.count())): 
            w = self.grid_layout.itemAt(i).widget()
            if w: w.setParent(None)
            
        courses = self.data_manager.get_courses()
        columns = 3
        
        for idx, course in enumerate(courses):
            # Use ElaAcrylicUrlCard
            card = ElaAcrylicUrlCard()
            card.set_title(course['name'])
            
            # Progress Logic
            videos = course.get('videos', [])
            watched_count = sum(1 for v in videos if v.get('completed', False))
            
            stats = course.get('stats', {})
            total = stats.get('total_videos', 0)
            
            progress = (watched_count / total * 100) if total > 0 else 0
            
            card.set_sub_title(f"进度: {watched_count}/{total} ({int(progress)}%)")
            
            # TODO: Set Card Image if available in course data, else placeholder
            # card.set_card_pixmap(...) 
            
            # Handling Click
            # ElaAcrylicUrlCard usually opens URL. We hijack it.
            # We disconnect internal slot connection in ElaAcrylicUrlCard? 
            # Or just connect clicked to our handler.
            card.clicked.connect(lambda checked=False, cid=course["id"]: self.course_selected.emit(cid))
            
            # Handling Right Click for Delete?
            # ElaAcrylicUrlCard is a QPushButton, right click might not emit custom signal.
            # We can subclass it locally or add event filter if needed.
            # For now, let's skip delete or add a context menu.
            card.setContextMenuPolicy(Qt.CustomContextMenu)
            card.customContextMenuRequested.connect(lambda pos, cid=course["id"]: self.show_context_menu(pos, cid))

            row = idx // columns
            col = idx % columns
            self.grid_layout.addWidget(card, row, col)

    def show_context_menu(self, pos, course_id):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        delete_action = menu.addAction("删除课程")
        action = menu.exec(QCursor.pos())
        if action == delete_action:
            self.confirm_delete(course_id)

    def confirm_delete(self, course_id):
        reply = QMessageBox.question(self, '确认删除', '确定要删除该课程吗？删除后数据不可恢复。', 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.delete_course(course_id)
            self.refresh_list()
