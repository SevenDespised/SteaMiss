from __future__ import annotations

import logging

from src.ui.infra.windowing.context import WindowContext


logger = logging.getLogger(__name__)


class InfoWindowBinder:
    """InfoWindow 绑定器：连接愿望单折扣 + 新闻加载。"""

    def bind(self, view: object, ctx: WindowContext) -> None:
        def update_window_data(games: list) -> None:
            view.update_data(games)

        ctx.steam_manager.on_wishlist_data.connect(update_window_data)
        view.request_refresh.connect(ctx.steam_manager.fetch_wishlist)

        cache = getattr(ctx.steam_manager, "cache", None) or {}
        if "wishlist" in cache:
            update_window_data(cache["wishlist"])
        else:
            ctx.steam_manager.fetch_wishlist()

        news_manager = getattr(ctx, "news_manager", None)
        if news_manager is not None:
            try:
                news_manager.on_news_data.connect(view.update_news_data)
            except Exception:
                logger.exception("InfoWindowBinder failed to connect news data")

            try:
                news_manager.on_error.connect(view.on_news_fetch_error)
            except Exception:
                logger.exception("InfoWindowBinder failed to connect news error")

            try:
                view.request_news_refresh.connect(lambda force, nm=news_manager: nm.fetch_news(force_refresh=bool(force)))
            except Exception:
                logger.exception("InfoWindowBinder failed to connect request_news_refresh")

            try:
                news_manager.fetch_news(force_refresh=False)
            except Exception:
                logger.exception("InfoWindowBinder failed to fetch news")

        epic_manager = getattr(ctx, "epic_manager", None)
        if epic_manager is not None:
            try:
                epic_manager.on_epic_free_games_data.connect(view.update_epic_free_games_data)
            except Exception:
                logger.exception("InfoWindowBinder failed to connect epic data")

            try:
                epic_manager.on_error.connect(lambda msg: view.update_epic_free_games_data([{"title": f"Epic 数据获取失败：{msg}", "period": "", "url": None}]))
            except Exception:
                logger.exception("InfoWindowBinder failed to connect epic error")

            # 优先使用缓存
            cached = []
            try:
                cached = epic_manager.last_items
            except Exception:
                cached = []

            if cached:
                try:
                    view.update_epic_free_games_data(cached)
                except Exception:
                    logger.exception("InfoWindowBinder failed to render cached epic data")

            # 每次打开 InfoWindow 都刷新一次（缓存仅用于秒开占位展示）。
            try:
                epic_manager.fetch_free_games()
            except Exception:
                logger.exception("InfoWindowBinder failed to fetch epic free games")


__all__ = ["InfoWindowBinder"]
