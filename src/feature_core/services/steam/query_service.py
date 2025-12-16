from __future__ import annotations

from typing import Any, Dict, List, Optional


class SteamQueryService:
    """
    Steam 查询子域（纯 Python）：
    - 从 cache 查询 primary 游戏缓存
    - recent/search 等纯查询能力

    边界：
    - 不读取 config（由 account/policy 决定 primary_id）
    - 不做聚合落 cache（由 aggregation/dataset 处理）
    """

    def get_primary_games_cache(self, cache: Dict[str, Any], primary_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not primary_id:
            return None
        if "games_primary" in cache:
            games_primary = cache.get("games_primary")
            return games_primary if isinstance(games_primary, dict) else None
        if "games" in cache:
            games = cache.get("games")
            return games if isinstance(games, dict) else None
        return None

    def get_recent_games(self, cache: Dict[str, Any], primary_id: Optional[str], limit: int = 3) -> List[dict]:
        games_cache = self.get_primary_games_cache(cache, primary_id)
        if not games_cache or not games_cache.get("all_games"):
            return []
        all_games = games_cache["all_games"]
        return sorted(all_games, key=lambda x: x.get("rtime_last_played", 0), reverse=True)[: int(limit or 0)]

    def search_games(self, cache: Dict[str, Any], primary_id: Optional[str], keyword: Optional[str]) -> List[dict]:
        games_cache = self.get_primary_games_cache(cache, primary_id)
        if not games_cache or not games_cache.get("all_games"):
            return []
        kw = (keyword or "").lower().strip()
        if not kw:
            return []

        results: List[dict] = []
        for game in games_cache["all_games"]:
            name = (game.get("name", "") or "").lower()
            if kw in name:
                results.append(game)
        return results


__all__ = ["SteamQueryService"]


