"""
交互菜单项构建器。
"""

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder
from src.feature_core.app.actions import Action


class InteractionMenuBuilder(BaseMenuBuilder):
    """打招呼和交互功能菜单项构建器"""

    def __init__(self, action_bus, config_manager, behavior_manager):
        super().__init__(action_bus, config_manager)
        self.behavior_manager = behavior_manager

    def build(self):
        ctx = getattr(self.behavior_manager, "interaction_context", None)

        # 无状态时：主选项是互动打招呼，无子选项
        if not ctx:
            return {
                "key": "interaction",
                "label": "互动：\n打招呼",
                "callback": lambda: self.action_bus.execute(Action.SAY_HELLO),
            }

        def _build_callback(action_value, kwargs):
            try:
                action = Action(action_value)
            except Exception:
                return None
            kwargs = kwargs or {}
            return lambda a=action, kw=kwargs: self.action_bus.execute(a, **kw)

        # 有状态时：主选项为上下文主动作，子选项里包含“互动打招呼”等
        item = {
            "key": "interaction",
            "label": ctx.get("label", "互动"),
            "callback": _build_callback(ctx.get("action"), ctx.get("kwargs")),
        }

        sub_items = []
        for sub in ctx.get("sub_items") or []:
            sub_items.append(
                {
                    "label": sub.get("label", ""),
                    "callback": _build_callback(sub.get("action"), sub.get("kwargs")),
                }
            )
        if sub_items:
            item["sub_items"] = sub_items

        return item


