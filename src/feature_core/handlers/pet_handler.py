from PyQt6.QtCore import QObject, pyqtSignal

class PetFeatureHandler(QObject):
    # 这里我们采用简单的回调/信号机制，让 FeatureRouter 依然作为信号中心
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

    def say_hello(self, **kwargs):
        if not self.config_manager: return None
        content = self.config_manager.get("say_hello_content", "你好！")
        return content # 返回内容，由 FeatureRouter 发射信号

