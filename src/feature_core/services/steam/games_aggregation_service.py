from __future__ import annotations

from typing import Any, Dict, Optional

from src.feature_core.services.steam.games_aggregator import merge_games


def _is_empty_games_payload(payload: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(payload, dict) or not payload:
        return True
    all_games = payload.get("all_games")
    if isinstance(all_games, list) and len(all_games) > 0:
        return False
    count = payload.get("count")
    if isinstance(count, int) and count > 0:
        return False
    return True


def _build_results_from_accounts(accounts: Dict[str, Any]) -> list[dict]:
    results: list[dict] = []
    for sid, entry in (accounts or {}).items():
        if not isinstance(entry, dict):
            continue
        games = entry.get("games")
        if not isinstance(games, dict):
            continue
        # 只要有任何有效 games payload 就计入（避免 merge 空覆盖）。
        all_games = games.get("all_games")
        count = games.get("count")
        if (isinstance(all_games, list) and all_games) or (isinstance(count, int) and count > 0):
            results.append({"steam_id": sid, "games": games, "summary": entry.get("summary")})
    return results


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
        account_map: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        summary_to_emit = None
        games_to_emit = None
        should_save = False

        if account_map:
            cache["games_accounts"] = account_map
            should_save = True

        if primary_id and account_map and primary_id in account_map:
            primary_summary = account_map[primary_id].get("summary")
            if primary_summary:
                cache["summary"] = primary_summary
                summary_to_emit = primary_summary
                should_save = True

        # games 完全源自 games_accounts：只要本次写入了 games_accounts，就据此重算并写回 games。
        if account_map:
            aggregated = merge_games(_build_results_from_accounts(account_map))
            if not _is_empty_games_payload(aggregated):
                cache["games"] = aggregated
                games_to_emit = aggregated
                should_save = True

        return {"summary_to_emit": summary_to_emit, "games_to_emit": games_to_emit, "should_save": should_save}

    def ensure_games_from_accounts(self, cache: Dict[str, Any]) -> bool:
        """启动/离线场景：若 games 缺失，则基于本地 games_accounts 聚合一次并写回 cache['games']。

        返回：是否需要保存到磁盘。
        """
        existing = cache.get("games")
        if isinstance(existing, dict) and not _is_empty_games_payload(existing):
            return False

        accounts = cache.get("games_accounts")
        if not isinstance(accounts, dict) or not accounts:
            return False

        aggregated = merge_games(_build_results_from_accounts(accounts))
        if _is_empty_games_payload(aggregated):
            return False

        cache["games"] = aggregated
        return True


__all__ = ["SteamGamesAggregationService"]


