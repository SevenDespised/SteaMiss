"""
计时器菜单项构建器。
"""

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder
from src.feature_core.app.actions import Action


class TimerMenuBuilder(BaseMenuBuilder):
    """计时器菜单项构建器"""

    def __init__(self, action_bus, config_manager, timer_handler):
        super().__init__(action_bus, config_manager)
        self.timer_handler = timer_handler

    def build(self):
        tm = self.timer_handler
        if not tm:
            return {"key": "timer", "label": "计时器\n未配置", "callback": lambda: None}

        if tm.is_running():
            return {
                "key": "timer",
                "label": "结束\n计时",
                "callback": lambda: self.action_bus.execute(Action.STOP_TIMER),
                "sub_items": [
                    {"label": "暂停\n计时", "callback": lambda: self.action_bus.execute(Action.PAUSE_TIMER)},
                    self._reminder_sub_item(),
                ],
            }
        if tm.is_paused():
            return {
                "key": "timer",
                "label": "结束\n计时",
                "callback": lambda: self.action_bus.execute(Action.STOP_TIMER),
                "sub_items": [
                    {"label": "继续\n计时", "callback": lambda: self.action_bus.execute(Action.RESUME_TIMER)},
                    self._reminder_sub_item(),
                ],
            }

        return {
            "key": "timer",
            "label": "开始\n计时",
            "callback": lambda: self.action_bus.execute(Action.TOGGLE_TIMER),
            "sub_items": [self._reminder_sub_item()],
        }

    def _reminder_sub_item(self):
        return {"label": "提醒\n设置", "callback": lambda: self.action_bus.execute(Action.OPEN_WINDOW, window_name="reminder_settings")}


__all__ = ["TimerMenuBuilder"]


