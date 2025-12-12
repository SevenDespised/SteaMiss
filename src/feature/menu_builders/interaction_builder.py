"""
交互菜单项构建器
"""
from .base_builder import BaseMenuBuilder


class InteractionMenuBuilder(BaseMenuBuilder):
    """打招呼和交互功能菜单项构建器"""
    
    def build(self):
        """构建交互菜单项"""
        # 动态获取置顶状态文本
        # 由于 FeatureRouter 不再持有 pet_window，这里无法直接获取状态
        # 临时方案：默认为“置顶/取消”，或者通过其他方式获取状态
        # 更好的方案是让 UIManager 在构建时传入状态，或者 FeatureRouter 提供状态查询接口（但这又会引入耦合）
        # 这里简化处理，显示通用文本，或者假设初始状态
        
        # TODO: 需要一个更好的方式来同步 UI 状态到菜单
        topmost_label = "切换\n置顶" 
        
        return {
            'key': 'say_hello',
            'label': '互动：\n打招呼',
            'callback': lambda: self.feature_router.execute_action("say_hello")
        }
