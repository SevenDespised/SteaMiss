from __future__ import annotations

from src.ui.infra.windowing.context import WindowContext


class AchievementWindowBinder:
    """AchievementWindow 绑定器：连接游戏库数据与成就统计数据。"""

    def bind(self, view: object, ctx: WindowContext) -> None:
        def update_window_data() -> None:
            datasets = ctx.steam_manager.get_game_datasets()
            achievements = ctx.steam_manager.cache.get("achievements", {}) if getattr(ctx.steam_manager, "cache", None) else {}
            view.update_data(datasets, achievements=achievements)

        ctx.steam_manager.on_games_stats.connect(update_window_data)
        ctx.steam_manager.on_achievements_data.connect(update_window_data)

        view.request_fetch_achievements.connect(ctx.steam_manager.fetch_achievements)

        update_window_data()


__all__ = ["AchievementWindowBinder"]


