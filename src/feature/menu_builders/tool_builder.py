"""
工具菜单项构建器
"""
from .base_builder import BaseMenuBuilder


class ToolMenuBuilder(BaseMenuBuilder):
    """统计、折扣等工具菜单项构建器"""
    
    def build_stats_item(self):
        """构建游玩记录菜单项，包含特惠推荐子菜单"""
        return {
            'key': 'stats',
            'label': '游玩统计',
            'callback': lambda: self.feature_manager.open_tool("stats"),
            'sub_items': [
                {
                    'key': 'discounts',
                    'label': '特惠推荐',
                    'callback': lambda: self.feature_manager.open_tool("discounts")
                },
                {
                    'key': 'achievements',
                    'label': '成就总览',
                    'callback': lambda: print('pass')
                }
            ]
        }
    
    def build_discounts_item(self):
        """构建特惠推荐菜单项 - 已移入游玩记录子菜单"""
        return None
