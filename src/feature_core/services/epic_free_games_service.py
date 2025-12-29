from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.feature_core.adapters.http.free_game_client import EpicFreeGameOffer, EpicFreeGamesClient


BEIJING_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


@dataclass(frozen=True)
class EpicFreeGamesSnapshot:
    updated_at_bjt: datetime
    current: list[EpicFreeGameOffer]
    upcoming: list[EpicFreeGameOffer]


class EpicFreeGamesService:
    """纯业务：拉取并统计 Epic 当前/即将免费游戏（时间按北京时间展示/计算）。"""

    def __init__(self, client: Optional[EpicFreeGamesClient] = None) -> None:
        self._client = client or EpicFreeGamesClient()

    def get_snapshot(
        self,
        *,
        locale: str = "zh-CN",
        country: str = "CN",
        allow_countries: str = "CN",
        now: Optional[datetime] = None,
    ) -> EpicFreeGamesSnapshot:
        now_bjt = self._ensure_bjt(now)
        current = self._client.get_current_free_games(
            locale=locale,
            country=country,
            allow_countries=allow_countries,
            now=now_bjt,
        )
        upcoming = self._client.get_upcoming_free_games(
            locale=locale,
            country=country,
            allow_countries=allow_countries,
            now=now_bjt,
        )
        return EpicFreeGamesSnapshot(updated_at_bjt=now_bjt, current=current, upcoming=upcoming)

    def build_info_window_items(self, snapshot: EpicFreeGamesSnapshot) -> list[dict]:
        """为 InfoWindow.epic_tab 生成 list[dict]，供 UI 侧 Epic 免费游戏列表展示。"""
        items: list[dict] = []

        def add_header(text: str) -> None:
            items.append({"title": text, "period": "", "url": None})

        updated = snapshot.updated_at_bjt.strftime("%Y-%m-%d %H:%M")
        add_header(f"统计：当前免费 {len(snapshot.current)} 个｜即将免费 {len(snapshot.upcoming)} 个（更新时间：{updated} 北京时间）")

        if snapshot.current:
            add_header(f"当前免费（{len(snapshot.current)}）")
            for o in snapshot.current:
                p = o.promotion
                period = f"{self._fmt_bjt(p.start_date)} - {self._fmt_bjt(p.end_date)}（北京时间）"
                items.append({"title": o.title, "period": period, "url": o.url})

        if snapshot.upcoming:
            add_header(f"即将免费（{len(snapshot.upcoming)}）")
            for o in snapshot.upcoming:
                p = o.promotion
                period = f"{self._fmt_bjt(p.start_date)} - {self._fmt_bjt(p.end_date)}（北京时间）"
                items.append({"title": o.title, "period": period, "url": o.url})

        if not snapshot.current and not snapshot.upcoming:
            items.append({"title": "暂无 Epic 免费游戏", "period": "", "url": None})

        return items

    def _fmt_bjt(self, dt: datetime) -> str:
        try:
            return dt.astimezone(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return ""

    def _ensure_bjt(self, dt: Optional[datetime]) -> datetime:
        if dt is None:
            return datetime.now(BEIJING_TZ)
        if dt.tzinfo is None:
            # 未指定时区则视为北京时间
            return dt.replace(tzinfo=BEIJING_TZ)
        return dt.astimezone(BEIJING_TZ)


__all__ = ["EpicFreeGamesService", "EpicFreeGamesSnapshot", "BEIJING_TZ"]
