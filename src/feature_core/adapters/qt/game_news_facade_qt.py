from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from src.feature_core.services.game_news_service import GameNewsService
from src.storage.news_repository import NewsRepository


logger = logging.getLogger(__name__)


class _GameNewsWorker(QThread):
    data_ready = pyqtSignal(dict)

    def __init__(self, service: GameNewsService, *, force_refresh: bool = False):
        super().__init__()
        self._service = service
        self._force_refresh = force_refresh

    def run(self) -> None:
        result: dict = {"type": "news", "data": None, "error": None}
        try:
            items, from_cache = self._service.get_news(force_refresh=self._force_refresh)
            result["data"] = {
                "items": [
                    {
                        "title": it.title,
                        "source": it.source,
                        "pub_date": _format_pub_date(it.published_at),
                        "link": it.url,
                        "summary": it.summary,
                    }
                    for it in items
                ],
                "from_cache": from_cache,
            }
        except Exception as e:
            logger.exception("GameNews worker failed: force_refresh=%s", self._force_refresh)
            result["error"] = str(e)
        self.data_ready.emit(result)


def _format_pub_date(dt: Optional[datetime]) -> str:
    if dt is None:
        return ""
    try:
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        logger.debug("Failed to format pub date", exc_info=True)
        return ""


class GameNewsFacadeQt(QObject):
    """Qt 对外入口：异步获取新闻，并向 UI 发射信号。"""

    on_news_data = pyqtSignal(list)
    on_error = pyqtSignal(str)

    def __init__(self, *, repository: Optional[NewsRepository] = None, service: Optional[GameNewsService] = None):
        super().__init__()
        self._repository = repository or NewsRepository()
        self._service = service or GameNewsService(self._repository)
        self._active_workers: list[_GameNewsWorker] = []

        try:
            self._repository.error_occurred.connect(self.on_error.emit)
        except Exception:
            logger.exception("Failed to connect NewsRepository.error_occurred")

    def fetch_news(self, *, force_refresh: bool = False) -> None:
        worker = _GameNewsWorker(self._service, force_refresh=force_refresh)
        worker.data_ready.connect(self._handle_result)
        worker.finished.connect(lambda: self._cleanup_worker(worker))

        self._active_workers.append(worker)
        worker.start()

    def _cleanup_worker(self, worker: _GameNewsWorker) -> None:
        if worker in self._active_workers:
            self._active_workers.remove(worker)

    def _handle_result(self, result: dict) -> None:
        if result.get("error"):
            logger.error("GameNews result error: %s", result.get("error"))
            self.on_error.emit(result["error"])
            return
        data = result.get("data") or {}
        items = data.get("items") or []
        if isinstance(items, list):
            self.on_news_data.emit(items)


__all__ = ["GameNewsFacadeQt"]
