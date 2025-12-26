from __future__ import annotations

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from src.feature_core.services.epic_free_games_service import EpicFreeGamesService


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

    def __init__(self, *, service: EpicFreeGamesService | None = None):
        super().__init__()
        self._service = service or EpicFreeGamesService()
        self._active_workers: list[_EpicFreeGamesWorker] = []
        self._last_items: list[dict] = []

    @property
    def last_items(self) -> list[dict]:
        return list(self._last_items)

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
            self.on_epic_free_games_data.emit(items)


__all__ = ["EpicFreeGamesFacadeQt"]
