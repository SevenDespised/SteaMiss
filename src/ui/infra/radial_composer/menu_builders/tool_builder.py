"""
工具菜单项构建器。
"""

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder
from src.feature_core.app.actions import Action


class ToolMenuBuilder(BaseMenuBuilder):
    """统计、折扣等工具菜单项构建器"""

    def build_stats_item(self):
        return {
            "key": "stats",
            "label": "游玩\n统计",
            "callback": lambda: self.action_bus.execute(Action.OPEN_WINDOW, window_name="stats"),
            "sub_items": [
                {"key": "discounts", "label": "特惠\n推荐", "callback": lambda: self.action_bus.execute(Action.OPEN_WINDOW, window_name="discounts")},
                {"key": "achievements", "label": "成就\n总览", "callback": lambda: self.action_bus.execute(Action.OPEN_WINDOW, window_name="achievements")},
            ],
        }


__all__ = ["ToolMenuBuilder"]


