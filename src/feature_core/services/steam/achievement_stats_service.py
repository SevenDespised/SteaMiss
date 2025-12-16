from __future__ import annotations

from typing import Any, Dict


def summarize_achievements(stats: Any) -> Dict[str, int]:
    """
    将 SteamClient.get_player_achievements() 的返回值汇总为 {total, unlocked}（纯 Python）。
    """
    if not isinstance(stats, dict):
        return {"total": 0, "unlocked": 0}
    ach_list = stats.get("achievements")
    if not isinstance(ach_list, list):
        return {"total": 0, "unlocked": 0}
    total = len(ach_list)
    unlocked = sum(1 for a in ach_list if isinstance(a, dict) and a.get("achieved") == 1)
    return {"total": total, "unlocked": unlocked}


__all__ = ["summarize_achievements"]


