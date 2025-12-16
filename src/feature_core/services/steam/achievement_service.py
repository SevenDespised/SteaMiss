from __future__ import annotations

from typing import Any, Dict


class SteamAchievementService:
    """
    Steam 成就子域（纯 Python）。
    只负责：将增量成就数据 merge 到 cache，并返回需要 emit 的增量数据。
    """

    def apply_achievements(self, cache: Dict[str, Any], achievements_delta: Dict[str, Any]) -> Dict[str, Any]:
        achievements = cache.get("achievements")
        if not isinstance(achievements, dict):
            achievements = {}
            cache["achievements"] = achievements
        achievements.update(achievements_delta)
        return {"achievements_to_emit": achievements_delta, "should_save": True}


__all__ = ["SteamAchievementService"]


