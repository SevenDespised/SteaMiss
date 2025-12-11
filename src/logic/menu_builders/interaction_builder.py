"""
交互菜单项构建器
"""
from .base_builder import BaseMenuBuilder


class InteractionMenuBuilder(BaseMenuBuilder):
    """打招呼和交互功能菜单项构建器"""
    
    def build(self):
        """构建交互菜单项"""
        # 动态获取置顶状态文本
        is_topmost = False
        if self.feature_manager.pet_window:
            is_topmost = self.feature_manager.pet_window.is_topmost()
        topmost_label = "取消\n置顶" if is_topmost else "置顶\n宠物"
        
        return {
            'key': 'say_hello',
            'label': '互动\n打招呼',
            'callback': lambda: self.feature_manager.execute_action("say_hello"),
            'sub_items': [
                {'label': '隐藏', 'callback': lambda: self.feature_manager.execute_action("hide_pet")},
                {'label': topmost_label, 'callback': lambda: self.feature_manager.execute_action("toggle_topmost")},
            ]
        }
