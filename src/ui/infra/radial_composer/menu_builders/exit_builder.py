"""
退出菜单项构建器。
"""

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder
from src.feature_core.app.actions import Action


class ExitMenuBuilder(BaseMenuBuilder):
    """退出菜单项构建器"""

    def build(self):
        topmost_label = "切换\n置顶"
        return {
            "key": "exit",
            "label": "退出",
            "callback": lambda: self.action_bus.execute(Action.EXIT),
            "sub_items": [
                {"label": "隐藏", "callback": lambda: self.action_bus.execute(Action.HIDE_PET)},
                {"label": topmost_label, "callback": lambda: self.action_bus.execute(Action.TOGGLE_TOPMOST)},
            ],
        }


__all__ = ["ExitMenuBuilder"]


