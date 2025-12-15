from PyQt6.QtCore import QObject, pyqtSignal
from src.feature_core.steam_support.steam_worker import SteamWorker

class SteamService(QObject):
    """
    Steam API 服务层
    负责管理 SteamWorker，执行异步任务
    """
    task_finished = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.active_workers = []

    def start_task(self, key, sid, task_type, extra_data=None, steam_id=None):
        """启动一个新的异步任务"""
        worker = SteamWorker(key, steam_id or sid, task_type, extra_data)
        worker.data_ready.connect(self._handle_result)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        
        self.active_workers.append(worker)
        worker.start()

    def _cleanup_worker(self, worker):
        if worker in self.active_workers:
            self.active_workers.remove(worker)

    def _handle_result(self, result):
        self.task_finished.emit(result)
