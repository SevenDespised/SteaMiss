import logging

from PyQt6.QtCore import QObject, pyqtSignal

from src.feature_core.adapters.qt.steam_worker_qt import SteamWorker


class SteamTaskServiceQt(QObject):
    """
    Steam 异步任务调度（Qt 适配）：
    - 管理 SteamWorker（QThread）
    - 发射 task_finished 信号给上层（SteamFacadeQt）
    """

    task_finished = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.active_workers = []

    def start_task(self, key, sid, task_type, extra_data=None, steam_id=None):
        worker = SteamWorker(key, steam_id or sid, task_type, extra_data)
        worker.data_ready.connect(self._handle_result)
        worker.finished.connect(lambda: self._cleanup_worker(worker))

        self.active_workers.append(worker)
        worker.start()

    def _cleanup_worker(self, worker):
        if worker in self.active_workers:
            self.active_workers.remove(worker)

    def _handle_result(self, result):
        try:
            logger = logging.getLogger(__name__)
            logger.debug(
                "SteamTaskServiceQt emit task_finished: type=%s keys=%s",
                (result or {}).get("type"),
                sorted(list((result or {}).keys())),
            )
            self.task_finished.emit(result)
        except Exception:
            logging.getLogger(__name__).exception(
                "SteamTaskServiceQt failed to emit task_finished: type=%s",
                (result or {}).get("type"),
            )


__all__ = ["SteamTaskServiceQt"]


