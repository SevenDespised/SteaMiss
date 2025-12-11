import os
import webbrowser
from PyQt6.QtWidgets import QApplication

class SystemFeatureHandler:
    def __init__(self, config_manager):
        self.config_manager = config_manager

    def open_explorer(self, path=None, **kwargs):
        if not self.config_manager: return
        
        if path is None:
            # 默认使用第一个配置的路径
            paths = self.config_manager.get("explorer_paths", ["C:/"])
            path = paths[0] if paths else "C:/"
            
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                raise Exception(f"Failed to open path {path}: {e}")
        else:
            raise Exception(f"Path not found: {path}")

    def open_url(self, url=None, **kwargs):
        if not url: return
        try:
            webbrowser.open(url)
        except Exception as e:
            raise Exception(f"Failed to open URL {url}: {e}")

    def exit_app(self, **kwargs):
        QApplication.instance().quit()
