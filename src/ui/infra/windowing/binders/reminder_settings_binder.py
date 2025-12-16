from __future__ import annotations

from src.ui.infra.windowing.context import WindowContext


class ReminderSettingsWindowBinder:
    """
    ReminderSettingsWindow 绑定器。

    说明：
    - 该窗口构造函数已直接注入 timer_handler；
    - 额外绑定目前不需要，但保留 binder 以统一注册结构。
    """

    def bind(self, view: object, ctx: WindowContext) -> None:
        _ = (view, ctx)
        return


__all__ = ["ReminderSettingsWindowBinder"]


