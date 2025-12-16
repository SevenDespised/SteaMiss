"""
交互菜单项构建器。
"""

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder


class InteractionMenuBuilder(BaseMenuBuilder):
    """打招呼和交互功能菜单项构建器"""

    def build(self):
        return {
            "key": "say_hello",
            "label": "互动：\n打招呼",
            "callback": lambda: self.feature_router.execute_action("say_hello"),
        }


__all__ = ["InteractionMenuBuilder"]


