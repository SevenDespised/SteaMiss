from PyQt6.QtCore import QObject, pyqtSignal

class PetFeatureHandler(QObject):
    # 信号需要在这里定义，因为 Handler 是实际执行者
    # 但为了保持 FeatureRouter 的接口一致性，我们可能需要通过 FeatureRouter 转发
    # 或者让 FeatureRouter 监听这些信号
    
    # 这里我们采用简单的回调/信号机制，让 FeatureRouter 依然作为信号中心
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

    def say_hello(self, **kwargs):
        if not self.config_manager: return None
        content = self.config_manager.get("say_hello_content", "你好！")
        return content # 返回内容，由 FeatureRouter 发射信号

