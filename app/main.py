"""CourseFlow 入口 — 依赖注入容器，组装并启动应用"""

import sys

from utils.env import setup_qt_env
from utils.paths import PathManager
from utils.logger import setup_logger
from utils.fonts import load_fonts, apply_global_font

from models.data_manager import DataManager
from services.theme_service import ThemeService
from controllers.main_controller import MainController


def main():
    # ---- 1. 环境准备 ----
    setup_qt_env()
    PathManager.ensure_dirs()

    logger = setup_logger("CourseFlow", PathManager.LOG_DIR)
    logger.info("=" * 50)
    logger.info("CourseFlow 启动中...")

    # ---- 2. Qt 应用（先创建，字体加载需要 QApplication） ----
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("CourseFlow")
    app.setOrganizationName("CourseFlow")

    # ---- 3. 字体加载 ----
    load_fonts()
    apply_global_font(app)

    # ---- 4. 依赖注入 ----
    theme_service = ThemeService(initial_theme="dark")
    data_manager = DataManager()
    controller = MainController(data_manager, theme_service)

    # ---- 5. 创建主窗口 ----
    from views.main_window import MainWindow
    window = MainWindow(controller)
    controller.set_view(window)

    # ---- 6. 启动 ----
    window.show()
    logger.info("CourseFlow 已启动")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
