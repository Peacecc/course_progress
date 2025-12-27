import os
import sys
import importlib.util

def setup_qt_env():
    """初始化 Qt 环境，确保 DLL 能被正确加载"""
    try:
        # 1. 寻找 PySide6 路径
        pyside6_spec = importlib.util.find_spec("PySide6")
        if not pyside6_spec: return
        
        pyside6_path = list(pyside6_spec.submodule_search_locations)[0]
        
        # 2. 注入 DLL 查找路径 (Python 3.8+)
        if sys.platform == 'win32':
            # 添加 PySide6 根目录 (包含核心 DLL)
            try:
                os.add_dll_directory(pyside6_path)
            except Exception: pass
            
            # 添加 shiboken6 路径
            shiboken6_spec = importlib.util.find_spec("shiboken6")
            if shiboken6_spec:
                shiboken6_path = list(shiboken6_spec.submodule_search_locations)[0]
                try:
                    os.add_dll_directory(shiboken6_path)
                except Exception: pass
            
            # 同时也添加到 PATH 以防万一 (旧版 Python 或某些第三方库)
            os.environ['PATH'] = pyside6_path + os.pathsep + os.environ['PATH']
            
        # 3. 设置插件路径
        plugin_path = os.path.join(pyside6_path, 'plugins')
        if os.path.exists(os.path.join(plugin_path, 'platforms')):
            os.environ['QT_PLUGIN_PATH'] = plugin_path
            
    except Exception as e:
        print(f"Env Setup Error: {e}")
