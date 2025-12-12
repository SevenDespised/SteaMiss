import json
import os
from PyQt6.QtCore import QObject, pyqtSignal

class SteamRepository(QObject):
    """
    Steam 数据持久化层
    负责本地数据的加载和保存
    """
    error_occurred = pyqtSignal(str)

    def __init__(self, data_file="config/steam_data.json"):
        super().__init__()
        self.data_file = data_file

    def load_data(self):
        """加载本地缓存数据"""
        cache = {}
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                print(f"Loaded local steam data from {self.data_file}")
            except Exception as e:
                msg = f"Failed to load local steam data: {e}"
                print(msg)
                self.error_occurred.emit(msg)
        return cache

    def save_data(self, data):
        """保存缓存数据到本地"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved steam data to {self.data_file}")
        except Exception as e:
            msg = f"Failed to save local steam data: {e}"
            print(msg)
            self.error_occurred.emit(msg)
