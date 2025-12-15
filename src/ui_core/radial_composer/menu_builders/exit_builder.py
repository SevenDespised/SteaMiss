"""
退出菜单项构建器
"""
from .base_builder import BaseMenuBuilder


class ExitMenuBuilder(BaseMenuBuilder):
    """退出菜单项构建器"""
    
    def build(self):
        """构建退出菜单项"""
        topmost_label = "切换\n置顶"
        
        return {
            'key': 'exit',
            'label': '退出',
            'callback': lambda: self.feature_router.execute_action("exit"),
            'sub_items': [
                {'label': '隐藏', 'callback': lambda: self.feature_router.execute_action("hide_pet")},
                {'label': topmost_label, 'callback': lambda: self.feature_router.execute_action("toggle_topmost")},
            ]
        }

