from __future__ import annotations

from typing import Any, Dict, List


def build_discounted_wishlist_items(wishlist_data: Dict[str, Any], limit: int = 10) -> List[dict]:
    """
    将 SteamClient.get_wishlist() 返回的 dict 结构转换为“折扣游戏列表”（纯 Python）。
    """
    discounted_games: List[dict] = []
    if not isinstance(wishlist_data, dict):
        return discounted_games

    for appid, details in wishlist_data.items():
        if not isinstance(details, dict):
            continue
        subs = details.get("subs", [])
        if not subs:
            continue

        best_sub = None
        max_discount = -1
        for sub in subs:
            if not isinstance(sub, dict):
                continue
            discount = sub.get("discount_pct", 0) or 0
            if discount > max_discount:
                max_discount = discount
                best_sub = sub

        if best_sub and max_discount > 0:
            discounted_games.append(
                {
                    "appid": appid,
                    "name": details.get("name", "Unknown"),
                    "discount_pct": max_discount,
                    "price": best_sub.get("price", ""),
                    "image": details.get("capsule", ""),
                }
            )

    discounted_games.sort(key=lambda x: x.get("discount_pct", 0), reverse=True)
    return discounted_games[: int(limit or 0)]


__all__ = ["build_discounted_wishlist_items"]


