from __future__ import annotations

from typing import Any, Dict


class SteamPriceService:
    """
    Steam 商店价格子域（纯 Python）。
    只负责：把增量价格 merge 到 cache，并返回需要 emit 的增量数据。
    """

    def apply_store_prices(self, cache: Dict[str, Any], prices_delta: Dict[str, Any]) -> Dict[str, Any]:
        prices = cache.get("prices")
        if not isinstance(prices, dict):
            prices = {}
            cache["prices"] = prices
        prices.update(prices_delta)
        return {"prices_to_emit": prices_delta, "should_save": True}


__all__ = ["SteamPriceService"]


