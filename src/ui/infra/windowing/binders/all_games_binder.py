from __future__ import annotations

from src.ui.infra.windowing.context import WindowContext


class AllGamesWindowBinder:
    """AllGamesWindow 绑定器：连接游戏库数据与价格数据。"""

    def bind(self, view: object, ctx: WindowContext) -> None:
        def update_window_data() -> None:
            datasets = ctx.steam_manager.get_game_datasets()
            prices = ctx.steam_manager.cache.get("prices", {}) if getattr(ctx.steam_manager, "cache", None) else {}
            view.update_data(datasets, prices=prices)

        ctx.steam_manager.on_games_stats.connect(update_window_data)
        ctx.steam_manager.on_store_prices.connect(update_window_data)

        view.request_fetch_prices.connect(ctx.steam_manager.fetch_store_prices)

        update_window_data()


__all__ = ["AllGamesWindowBinder"]


