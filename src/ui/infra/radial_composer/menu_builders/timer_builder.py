"""
计时器菜单项构建器。
"""

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder


class TimerMenuBuilder(BaseMenuBuilder):
    """计时器菜单项构建器"""

    def __init__(self, feature_router, config_manager, timer_handler):
        super().__init__(feature_router, config_manager)
        self.timer_handler = timer_handler

    def build(self):
        tm = self.timer_handler
        if not tm:
            return {"key": "timer", "label": "计时器\n未配置", "callback": lambda: None}

        if tm.is_running():
            return {
                "key": "timer",
                "label": "结束\n计时",
                "callback": lambda: self.feature_router.execute_action("stop_timer"),
                "sub_items": [
                    {"label": "暂停\n计时", "callback": lambda: self.feature_router.execute_action("pause_timer")},
                    self._reminder_sub_item(),
                ],
            }
        if tm.is_paused():
            return {
                "key": "timer",
                "label": "结束\n计时",
                "callback": lambda: self.feature_router.execute_action("stop_timer"),
                "sub_items": [
                    {"label": "继续\n计时", "callback": lambda: self.feature_router.execute_action("resume_timer")},
                    self._reminder_sub_item(),
                ],
            }

        return {
            "key": "timer",
            "label": "开始\n计时",
            "callback": lambda: self.feature_router.execute_action("toggle_timer"),
            "sub_items": [self._reminder_sub_item()],
        }

    def _reminder_sub_item(self):
        return {"label": "提醒\n设置", "callback": lambda: self.feature_router.open_window("reminder_settings")}


__all__ = ["TimerMenuBuilder"]


