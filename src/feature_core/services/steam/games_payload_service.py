from __future__ import annotations

from typing import Any, Dict, List


def build_games_payload(games: List[Dict[str, Any]], game_count: int) -> Dict[str, Any]:
    """
    将 owned_games 的原始 games 列表整形成 UI/聚合更容易消费的 payload（纯 Python）。
    """
    games_by_playtime = sorted(games, key=lambda x: x.get("playtime_forever", 0), reverse=True)
    games_by_recent = sorted(games, key=lambda x: x.get("rtime_last_played", 0), reverse=True)
    games_by_2weeks = sorted(games, key=lambda x: x.get("playtime_2weeks", 0), reverse=True)
    top_2weeks = [g for g in games_by_2weeks if g.get("playtime_2weeks", 0) > 0][:5]

    return {
        "count": game_count,
        "all_games": games,
        "top_games": games_by_playtime[:5],
        "recent_game": games_by_recent[0] if games_by_recent else None,
        "top_2weeks": top_2weeks,
        "total_playtime": sum(g.get("playtime_forever", 0) for g in games),
    }


__all__ = ["build_games_payload"]


