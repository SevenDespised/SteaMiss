from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Callable, Optional

from src.feature_core.adapters.http.game_news_client import GameNewsClient, NewsItem, NewsSource
from src.storage.news_repository import NewsRepository


class GameNewsService:
    """新闻业务服务：负责按“日期”缓存策略读取/刷新新闻。"""

    def __init__(
        self,
        repository: NewsRepository,
        client: Optional[GameNewsClient] = None,
        *,
        sources: Optional[list[NewsSource]] = None,
        today_provider: Optional[Callable[[], date]] = None,
    ) -> None:
        self._repository = repository
        self._client = client or GameNewsClient()
        self._sources = sources or self._default_sources()
        self._today_provider = today_provider or (lambda: date.today())

    def get_news(self, *, force_refresh: bool = False) -> tuple[list[NewsItem], bool]:
        """获取新闻。

        Returns:
            (items, from_cache)
        """
        cached_date_str, cached_items = self._repository.load_cached_items()
        today_str = self._today_provider().isoformat()

        if not force_refresh and cached_date_str == today_str and cached_items:
            return (self._items_from_dicts(cached_items), True)

        try:
            items = self._client.fetch_sources(self._sources, per_source_limit=20, total_limit=60)
            self._repository.save_cached_items(today_str, [self._item_to_dict(it) for it in items])
            return (items, False)
        except Exception:
            # 抓取失败：如果本地有旧缓存，则降级使用旧缓存
            if cached_items:
                return (self._items_from_dicts(cached_items), True)
            raise

    def _default_sources(self) -> list[NewsSource]:
        # 默认源：保持最小集合，后续如需可挪到 settings.json 配置
        return [
            NewsSource(name="机核", feed_url="https://www.gcores.com/rss"),
            NewsSource(name="GameSpot", feed_url="https://www.gamespot.com/feeds/news/"),
            NewsSource(name="游研社", feed_url="https://www.yystv.cn/rss/feed"),
        ]

    def _item_to_dict(self, item: NewsItem) -> dict:
        d = asdict(item)
        # datetime 需要序列化
        if item.published_at is not None:
            d["published_at"] = item.published_at.isoformat()
        else:
            d["published_at"] = None
        return d

    def _items_from_dicts(self, rows: list[dict]) -> list[NewsItem]:
        items: list[NewsItem] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            items.append(
                NewsItem(
                    title=str(row.get("title") or ""),
                    url=str(row.get("url") or ""),
                    published_at=None,  # UI 展示不强依赖；需要可后续解析
                    summary=str(row.get("summary") or ""),
                    source=str(row.get("source") or ""),
                )
            )
        return items


__all__ = ["GameNewsService"]
