from PyQt6.QtCore import QObject, pyqtSignal

class PetFeatureHandler(QObject):
    # 信号需要在这里定义，因为 Handler 是实际执行者
    # 但为了保持 FeatureManager 的接口一致性，我们可能需要通过 FeatureManager 转发
    # 或者让 FeatureManager 监听这些信号
    
    # 这里我们采用简单的回调/信号机制，让 FeatureManager 依然作为信号中心
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

    def say_hello(self, **kwargs):
        if not self.config_manager: return None
        content = self.config_manager.get("say_hello_content", "你好！")
        return content # 返回内容，由 FeatureManager 发射信号

    # hide_pet 和 toggle_topmost 实际上是纯信号触发，
    # 逻辑在 Application/UIManager 中处理，Handler 这里其实没什么业务逻辑可写
    # 但为了统一，我们还是保留接口
