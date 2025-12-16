from __future__ import annotations

from src.ui.infra.windowing.context import WindowContext


class StatsWindowBinder:
    """
    StatsWindow 绑定器：连接 SteamManager 信号/请求，并处理窗口内部跳转意图。
    """

    def bind(self, view: object, ctx: WindowContext) -> None:
        def update_window_data() -> None:
            datasets = ctx.steam_manager.get_game_datasets()
            fallback_summary = ctx.steam_manager.cache.get("summary") if getattr(ctx.steam_manager, "cache", None) else None
            view.update_data(datasets, fallback_summary, ctx.steam_manager.config)

        ctx.steam_manager.on_player_summary.connect(update_window_data)
        ctx.steam_manager.on_games_stats.connect(update_window_data)

        view.request_refresh.connect(ctx.steam_manager.fetch_player_summary)
        view.request_refresh.connect(ctx.steam_manager.fetch_games_stats)

        if callable(ctx.navigate):
            try:
                view.request_open_all_games.connect(lambda: ctx.navigate("all_games"))
            except Exception:
                pass

        update_window_data()


__all__ = ["StatsWindowBinder"]


