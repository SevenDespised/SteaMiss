from __future__ import annotations

from src.ui.infra.windowing.context import WindowContext


class DiscountWindowBinder:
    """DiscountWindow 绑定器：连接愿望单数据刷新。"""

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


__all__ = ["DiscountWindowBinder"]


