from typing import List, Dict, Any, Optional

class GamesAggregator:
    """管理多账号游戏统计的聚合上下文"""

    def __init__(self):
        self._ctx = None

    def begin(self, account_ids: List[str], primary_id: str):
        self._ctx = {
            "pending": len(account_ids),
            "primary": primary_id,
            "results": [],
        }

    def add_result(self, steam_id: str, data: Dict[str, Any]) -> bool:
        if not self._ctx:
            return False
        self._ctx["results"].append({"steam_id": steam_id, "data": data})
        self._ctx["pending"] -= 1
        return self._ctx["pending"] <= 0

    def mark_error(self) -> bool:
        if not self._ctx:
            return False
        self._ctx["pending"] -= 1
        return self._ctx["pending"] <= 0

    def finalize(self):
        if not self._ctx:
            return None, None

        results = self._ctx["results"]
        primary_id = self._ctx.get("primary")
        self._ctx = None

        primary_data = pick_primary_results(results, primary_id)
        aggregated = merge_games(results)
        return primary_data, aggregated


def pick_primary_results(results: List[Dict[str, Any]], primary_id: Optional[str]):
    primary_data = None
    if primary_id:
        for item in results:
            if item.get("steam_id") == primary_id:
                primary_data = item.get("data")
                break

    if primary_data is None and results:
        primary_data = results[0].get("data")
    return primary_data


def merge_games(results: List[Dict[str, Any]]):
    merged: Dict[Any, Dict[str, Any]] = {}

    for item in results:
        data = item.get("data") or {}
        for game in data.get("all_games", []):
            appid = game.get("appid")
            if appid is None:
                continue

            if appid not in merged:
                merged[appid] = {
                    "appid": appid,
                    "name": game.get("name", "Unknown"),
                    "playtime_forever": 0,
                    "playtime_2weeks": 0,
                    "rtime_last_played": game.get("rtime_last_played", 0),
                }

            merged[appid]["playtime_forever"] += game.get("playtime_forever", 0)
            merged[appid]["playtime_2weeks"] += game.get("playtime_2weeks", 0)
            merged[appid]["rtime_last_played"] = max(
                merged[appid].get("rtime_last_played", 0),
                game.get("rtime_last_played", 0),
            )

    all_games = list(merged.values())

    total_playtime = sum(g.get("playtime_forever", 0) for g in all_games)

    games_by_playtime = sorted(all_games, key=lambda x: x.get("playtime_forever", 0), reverse=True)
    games_by_recent = sorted(all_games, key=lambda x: x.get("rtime_last_played", 0), reverse=True)
    games_by_2weeks = sorted(all_games, key=lambda x: x.get("playtime_2weeks", 0), reverse=True)
    top_2weeks = [g for g in games_by_2weeks if g.get("playtime_2weeks", 0) > 0][:5]

    return {
        "count": len(all_games),
        "all_games": all_games,
        "top_games": games_by_playtime[:5],
        "recent_game": games_by_recent[0] if games_by_recent else None,
        "top_2weeks": top_2weeks,
        "total_playtime": total_playtime,
    }
