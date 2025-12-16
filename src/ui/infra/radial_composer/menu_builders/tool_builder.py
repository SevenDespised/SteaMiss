"""
工具菜单项构建器。
"""

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder


class ToolMenuBuilder(BaseMenuBuilder):
    """统计、折扣等工具菜单项构建器"""

    def build_stats_item(self):
        return {
            "key": "stats",
            "label": "游玩\n统计",
            "callback": lambda: self.feature_router.open_window("stats"),
            "sub_items": [
                {"key": "discounts", "label": "特惠\n推荐", "callback": lambda: self.feature_router.open_window("discounts")},
                {"key": "achievements", "label": "成就\n总览", "callback": lambda: self.feature_router.open_window("achievements")},
            ],
        }


__all__ = ["ToolMenuBuilder"]


