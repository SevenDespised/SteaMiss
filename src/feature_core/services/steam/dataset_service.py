from __future__ import annotations

from typing import Any, Dict, List, Optional


class SteamDatasetService:
    """
    Steam 数据集（Tabs）子域（纯 Python）：
    - build_game_datasets：将 cache → UI 可消费 datasets 列表

    边界：
    - 不读取 config（由 account/policy 提供 primary_id/alt_ids）
    - 不处理 worker result（由 facade + aggregation/profile/... 子域处理）
    """


    def build_game_datasets(self, cache: Dict[str, Any], primary_id: Optional[str], alt_ids: Any) -> List[dict]:
        datasets: List[dict] = []

        games_total: Optional[Dict[str, Any]] = cache.get("games")
        if not games_total:
            games_total = {"count": 0, "all_games": []}
        datasets.append({"key": "total", "label": "总计", "steam_id": None, "data": games_total, "summary": None})

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


