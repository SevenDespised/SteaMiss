from __future__ import annotations

from typing import Any, Dict, List


class SteamWishlistService:
    """
    Steam 愿望单子域（纯 Python）。
    只负责：更新 cache 并返回需要 emit 的数据。
    """

    def apply_wishlist(self, cache: Dict[str, Any], wishlist: List[dict]) -> Dict[str, Any]:
        cache["wishlist"] = wishlist
        return {"wishlist_to_emit": wishlist, "should_save": True}


__all__ = ["SteamWishlistService"]


