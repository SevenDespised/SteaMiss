from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from src.feature_core.services.epic_free_games_service import EpicFreeGamesService


logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from src.feature_core.adapters.qt.steam_facade_qt import SteamFacadeQt


class _EpicFreeGamesWorker(QThread):
    data_ready = pyqtSignal(dict)

    def __init__(self, service: EpicFreeGamesService):
        super().__init__()
        self._service = service

    def run(self) -> None:
        result: dict = {"type": "epic_free_games", "data": None, "error": None}
        try:
            snapshot = self._service.get_snapshot(locale="zh-CN", country="CN", allow_countries="CN")
            items = self._service.build_info_window_items(snapshot)
            result["data"] = {"items": items}
        except Exception as e:
            result["error"] = str(e)
        self.data_ready.emit(result)


class EpicFreeGamesFacadeQt(QObject):
    """Qt 对外入口：异步获取 Epic 免费游戏，并向 UI 发射信号。"""

    on_epic_free_games_data = pyqtSignal(list)
    on_error = pyqtSignal(str)

    def __init__(
        self,
        *,
        service: EpicFreeGamesService | None = None,
        steam_manager: "SteamFacadeQt | None" = None,
        cache_key: str = "free_game",
    ):
        super().__init__()
        self._service = service or EpicFreeGamesService()
        self._active_workers: list[_EpicFreeGamesWorker] = []
        self._last_items: list[dict] = []
        self._steam_manager = steam_manager
        self._cache_key = cache_key

        self._load_cached_from_game_data()

    @property
    def last_items(self) -> list[dict]:
        return list(self._last_items)

    def _load_cached_from_game_data(self) -> None:
        """从共享 game data 缓存加载 Epic 免费游戏列表。
        """
        sm = self._steam_manager
        if sm is None:
            return
        cache = getattr(sm, "cache", None)
        if not isinstance(cache, dict):
            return

        payload = cache.get(self._cache_key)
        if not isinstance(payload, dict):
            return
        items = payload.get("items")
        if isinstance(items, list):
            self._last_items = items

    def fetch_free_games(self) -> None:
        worker = _EpicFreeGamesWorker(self._service)
        worker.data_ready.connect(self._handle_result)
        worker.finished.connect(lambda: self._cleanup_worker(worker))

        self._active_workers.append(worker)
        worker.start()

    def _cleanup_worker(self, worker: _EpicFreeGamesWorker) -> None:
        if worker in self._active_workers:
            self._active_workers.remove(worker)

    def _handle_result(self, result: dict) -> None:
        if result.get("error"):
            self.on_error.emit(result["error"])
            return

        data = result.get("data") or {}
        items = data.get("items") or []
        if isinstance(items, list):
            self._last_items = items
            self._persist_to_game_data(items)
            self.on_epic_free_games_data.emit(items)

    def _persist_to_game_data(self, items: list[dict]) -> None:
        sm = self._steam_manager
        if sm is None:
            return

        cache = getattr(sm, "cache", None)
        repo = getattr(sm, "repository", None)
        if not isinstance(cache, dict) or repo is None:
            return
        save_data = getattr(repo, "save_data", None)
        if not callable(save_data):
            return

        try:
            cache[self._cache_key] = {
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "items": items,
            }
            save_data(cache)
        except Exception as e:
            logger.exception("Failed to persist epic free games into game data")
            try:
                self.on_error.emit(str(e))
            except Exception:
                logger.exception("Failed to emit epic persist error")


__all__ = ["EpicFreeGamesFacadeQt"]
