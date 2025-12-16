"""
交互菜单项构建器。
"""

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder
from src.feature_core.app.actions import Action


class InteractionMenuBuilder(BaseMenuBuilder):
    """打招呼和交互功能菜单项构建器"""

    def build(self):
        return {
            "key": "say_hello",
            "label": "互动：\n打招呼",
            "callback": lambda: self.action_bus.execute(Action.SAY_HELLO),
        }


__all__ = ["InteractionMenuBuilder"]


