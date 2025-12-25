from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


class PetService:
    """
    宠物用例/业务服务（纯 Python，不依赖 Qt）。

    当前阶段：只提供“打招呼文案”的读取。
    后续可在这里逐步扩展：
    - 宠物数值计算（可下沉到 domain）
    - 行为决策/行为队列（services）
    - 与 UI 的交互通过 UiIntentsQt / PetFacadeQt 完成
    """

    SAY_HELLO_FALLBACK_TEXT = "你好！"

    def __init__(self) -> None:
        pass

    def build_say_hello_prompt(self, prompt_manager: object, steam_manager: Optional[object] = None) -> str:
        """构建 say_hello 的 LLM Prompt。

        - 从 steam_manager.cache 读取 summary / games 缓存（若存在）
        - 组装为 PromptManager 的 say_hello 模板 kwargs
        - 返回 prompt_manager.get_prompt("say_hello", **kwargs)
        """
        kwargs = self._build_say_hello_kwargs(steam_manager)
        try:
            get_prompt = getattr(prompt_manager, "get_prompt")
        except Exception:
            return ""
        return get_prompt("say_hello", **kwargs)

    def _build_say_hello_kwargs(self, steam_manager: Optional[object]) -> Dict[str, Any]:
        now = datetime.now()
        current_datetime = now.strftime("%Y-%m-%d %H:%M")

        summary: Dict[str, Any] = {}
        cache: Dict[str, Any] = {}
        if steam_manager is not None:
            cache = getattr(steam_manager, "cache", {}) or {}
            if isinstance(cache, dict):
                maybe_summary = cache.get("summary")
                if isinstance(maybe_summary, dict):
                    summary = maybe_summary

        persona_name = (summary.get("personaname") or "未知")

        steam_level = self._steam_level(summary)
        total_playtime_hours = self._total_playtime_hours(cache)

        last_logoff = self._ts_to_text(summary.get("lastlogoff"))
        time_created = self._ts_to_text(summary.get("timecreated"))
        account_age_days = self._account_age_days(summary.get("timecreated"))

        owned_games_count = self._owned_games_count(cache)
        recent_games = self._recent_games_brief(steam_manager)

        # 确保所有模板字段都有值，避免 format KeyError 导致降级
        return {
            "current_datetime": current_datetime,
            "persona_name": persona_name,
            "steam_level": steam_level,
            "total_playtime_hours": total_playtime_hours,
            "recent_games": recent_games,
            "owned_games_count": owned_games_count,
            "last_logoff": last_logoff,
            "time_created": time_created,
            "account_age_days": account_age_days,
        }

    def _steam_level(self, summary: Dict[str, Any]) -> str:
        try:
            level = summary.get("steam_level")
            if level is None:
                return "?"
            return str(int(level))
        except Exception:
            return "?"

    def _total_playtime_hours(self, cache: Dict[str, Any]) -> str:
        """从 cache 中读取 total_playtime（分钟）并转换为小时文本。"""
        try:
            total_games = self._get_total_games(cache)
            if not total_games:
                return "未知"

            total_min = total_games.get("total_playtime")
            if total_min is None:
                return "未知"

            total_min_int = int(total_min)
            if total_min_int < 0:
                return "未知"
            return str(int(total_min_int / 60))
        except Exception:
            return "未知"

    def _ts_to_text(self, ts: Any) -> str:
        try:
            if ts is None:
                return "未知"
            ts_int = int(ts)
            if ts_int <= 0:
                return "未知"
            return datetime.fromtimestamp(ts_int).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return "未知"

    def _account_age_days(self, time_created_ts: Any) -> str:
        try:
            if time_created_ts is None:
                return "未知"
            ts_int = int(time_created_ts)
            if ts_int <= 0:
                return "未知"
            days = int((datetime.now().timestamp() - ts_int) // (24 * 3600))
            return str(max(days, 0))
        except Exception:
            return "未知"

    def _owned_games_count(self, cache: Dict[str, Any]) -> str:
        try:
            total_games = self._get_total_games(cache)
            if not total_games:
                return "未知"

            count = total_games.get("count")
            if count is not None:
                return str(int(count))
            all_games = total_games.get("all_games")
            if isinstance(all_games, list):
                return str(len(all_games))
            return "未知"
        except Exception:
            return "未知"

    def _get_total_games(self, cache: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """读取“总计”游戏 payload。
        """
        cached = cache.get("games")
        if isinstance(cached, dict) and (cached.get("all_games") is not None or cached.get("count") is not None):
            return cached
        return None

    def _recent_games_brief(self, steam_manager: Optional[object]) -> str:
        if steam_manager is None:
            return "未知"
        try:
            cache = getattr(steam_manager, "cache", None)
            if not isinstance(cache, dict):
                return "未知"
            total_games = self._get_total_games(cache)
            if not total_games or not total_games.get("all_games"):
                return "无"
            all_games = total_games.get("all_games") or []
            games = sorted(all_games, key=lambda x: (x or {}).get("rtime_last_played", 0), reverse=True)[:3]
            names = []
            for g in games:
                name = g.get("name") if isinstance(g, dict) else None
                if name:
                    names.append(str(name))
            return "、".join(names) if names else "无"
        except Exception:
            return "未知"

    def get_say_hello_fallback_text(self) -> str:
        """LLM 失败/不可用时的回退文案（唯一保留的默认值）。"""
        return self.SAY_HELLO_FALLBACK_TEXT


__all__ = ["PetService"]


