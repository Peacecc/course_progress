import sys
from app.utils.env import setup_qt_env

def main():
    # 1. 环境准备
    setup_qt_env()
    
    # 2. 启动应用
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 3. MVC 初始化
    from app.controllers.main_controller import MainController
    from app.views.main_window import MainWindow
    
    controller = MainController()
    window = MainWindow(controller)
    controller.set_view(window)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
