from __future__ import annotations

from typing import Optional

from src.ui.infra.windowing.context import WindowContext
from src.ui.infra.windowing.registry import WindowRegistry, WindowSpec
from src.ui.infra.windowing.binders.achievement_binder import AchievementWindowBinder
from src.ui.infra.windowing.binders.all_games_binder import AllGamesWindowBinder
from src.ui.infra.windowing.binders.discount_binder import DiscountWindowBinder
from src.ui.infra.windowing.binders.reminder_settings_binder import ReminderSettingsWindowBinder
from src.ui.infra.windowing.binders.settings_dialog_binder import SettingsDialogBinder
from src.ui.infra.windowing.binders.stats_binder import StatsWindowBinder


def build_window_registry() -> WindowRegistry:
    """
    构建默认 WindowRegistry。

    约定：
    - create 内做惰性 import（减少启动导入成本）
    - binder 负责信号绑定与首次刷新
    """
    registry = WindowRegistry()

    def create_settings(ctx: WindowContext, parent: Optional[object] = None) -> object:
        from src.ui.windows.settings_dialog import SettingsDialog

        return SettingsDialog(prompt_manager=ctx.prompt_manager, parent=parent)

    def create_stats(ctx: WindowContext, parent: Optional[object] = None) -> object:
        from src.ui.windows.stats_window import StatsWindow

        _ = (ctx, parent)
        return StatsWindow(parent=parent)

    def create_all_games(ctx: WindowContext, parent: Optional[object] = None) -> object:
        from src.ui.windows.all_games_window import AllGamesWindow

        return AllGamesWindow(parent=parent)

    def create_discounts(ctx: WindowContext, parent: Optional[object] = None) -> object:
        from src.ui.windows.discount_window import DiscountWindow

        _ = (ctx, parent)
        return DiscountWindow(parent=parent)

    def create_achievements(ctx: WindowContext, parent: Optional[object] = None) -> object:
        from src.ui.windows.achievement_window import AchievementWindow

        return AchievementWindow(parent=parent)

    def create_reminder_settings(ctx: WindowContext, parent: Optional[object] = None) -> object:
        from src.ui.windows.reminder_settings_window import ReminderSettingsWindow

        return ReminderSettingsWindow(ctx.timer_handler, parent=parent)

    registry.register("settings", WindowSpec(create=create_settings, binder=SettingsDialogBinder()))
    registry.register("stats", WindowSpec(create=create_stats, binder=StatsWindowBinder()))
    registry.register("all_games", WindowSpec(create=create_all_games, binder=AllGamesWindowBinder()))
    registry.register("discounts", WindowSpec(create=create_discounts, binder=DiscountWindowBinder()))
    registry.register("achievements", WindowSpec(create=create_achievements, binder=AchievementWindowBinder()))
    registry.register("reminder_settings", WindowSpec(create=create_reminder_settings, binder=ReminderSettingsWindowBinder()))

    return registry


__all__ = ["build_window_registry"]


