from __future__ import annotations

from typing import Any, Dict, Optional


class SteamProfileService:
    """
    Steam 个人资料/summary 子域（纯 Python）。
    只负责：更新 cache、产出需要 emit 的数据与是否需要持久化。
    """

    def apply_summary(self, cache: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        cache["summary"] = summary
        return {"summary_to_emit": summary, "should_save": True}


__all__ = ["SteamProfileService"]


