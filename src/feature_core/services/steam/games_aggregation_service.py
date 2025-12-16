from __future__ import annotations

from typing import Any, Dict, Optional


class SteamGamesAggregationService:
    """
    Steam games 聚合落 cache 子域（纯 Python）：
    - 将 games_aggregator.finalize() 的结果写回 cache
    - 返回需要 emit 的数据与是否需要 save
    """

    def apply_games_aggregation(
        self,
        cache: Dict[str, Any],
        primary_id: Optional[str],
        primary_data: Optional[Dict[str, Any]],
        aggregated: Optional[Dict[str, Any]],
        account_map: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        summary_to_emit = None
        games_to_emit = None
        should_save = False

        if account_map:
            cache["games_accounts"] = account_map
            should_save = True

        if primary_data:
            cache["games_primary"] = primary_data
            should_save = True

        if primary_id and account_map and primary_id in account_map:
            primary_summary = account_map[primary_id].get("summary")
            if primary_summary:
                cache["summary"] = primary_summary
                summary_to_emit = primary_summary
                should_save = True

        if aggregated is not None:
            cache["games"] = aggregated
            games_to_emit = aggregated
            should_save = True

        return {"summary_to_emit": summary_to_emit, "games_to_emit": games_to_emit, "should_save": should_save}


__all__ = ["SteamGamesAggregationService"]


