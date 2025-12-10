"""
工具菜单项构建器
"""
from .base_builder import BaseMenuBuilder


class ToolMenuBuilder(BaseMenuBuilder):
    """统计、折扣等工具菜单项构建器"""
    
    def build_stats_item(self):
        """构建游玩记录菜单项"""
        return {
            'key': 'stats',
            'label': '游玩记录',
            'callback': lambda: self.tool_manager.open_tool("stats")
        }
    
    def build_discounts_item(self):
        """构建特惠推荐菜单项"""
        return {
            'key': 'discounts',
            'label': '特惠推荐',
            'callback': lambda: self.tool_manager.open_tool("discounts")
        }
