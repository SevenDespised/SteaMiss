from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.feature_core.services.steam.games_aggregator import merge_games


class SteamDatasetService:
    """
    Steam 数据集（Tabs）子域（纯 Python）：
    - ensure_aggregated_cache：保证 cache['games'] 总计聚合存在
    - build_game_datasets：将 cache → UI 可消费 datasets 列表

    边界：
    - 不读取 config（由 account/policy 提供 primary_id/alt_ids）
    - 不处理 worker result（由 facade + aggregation/profile/... 子域处理）
    """

    def ensure_aggregated_cache(self, cache: Dict[str, Any]) -> None:
        accounts = cache.get("games_accounts", {}) or {}
        if not isinstance(accounts, dict) or not accounts:
            cache.pop("games", None)
            return

        results = []
        for sid, data in accounts.items():
            if isinstance(data, dict) and data.get("games"):
                results.append({"steam_id": sid, "games": data["games"], "summary": data.get("summary")})
        if results:
            cache["games"] = merge_games(results)
        else:
            cache.pop("games", None)

    def build_game_datasets(self, cache: Dict[str, Any], primary_id: Optional[str], alt_ids: Any) -> List[dict]:
        datasets: List[dict] = []
        self.ensure_aggregated_cache(cache)

        aggregated = cache.get("games")
        if aggregated is not None:
            datasets.append({"key": "total", "label": "总计", "steam_id": None, "data": aggregated, "summary": None})

        accounts = dict(cache.get("games_accounts", {}) or {})
        if primary_id and primary_id in accounts:
            primary_entry = accounts[primary_id]
            games_data = primary_entry.get("games") if isinstance(primary_entry, dict) else None
            if games_data:
                datasets.append(
                    {
                        "key": "primary",
                        "label": "主账号",
                        "steam_id": primary_id,
                        "data": games_data,
                        "summary": primary_entry.get("summary") if isinstance(primary_entry, dict) else None,
                    }
                )

        if isinstance(alt_ids, list):
            sub_index = 1
            for sid in alt_ids:
                entry = accounts.get(sid)
                if isinstance(entry, dict) and entry.get("games"):
                    datasets.append(
                        {
                            "key": f"sub_{sub_index}",
                            "label": f"子账号{sub_index}",
                            "steam_id": sid,
                            "data": entry.get("games"),
                            "summary": entry.get("summary"),
                        }
                    )
                    sub_index += 1
        return datasets


__all__ = ["SteamDatasetService"]


