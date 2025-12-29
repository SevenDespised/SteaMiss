from __future__ import annotations

import datetime
import logging
import os
from typing import Any, Callable, Optional

from PyQt6.QtCore import QTimer, QObject, pyqtSignal

from src.storage.timer_log_repository import TimerLogRepository
from src.storage.timer_settings_repository import TimerSettingsRepository
from src.feature_core.domain.timer_models import ReminderSettings
from src.feature_core.services.timer_service import TickResult, TimerService


logger = logging.getLogger(__name__)


class TimerFacadeQt(QObject):
    """
    Qt 对外入口：TimerFacadeQt
    - 用 QTimer 驱动 tick
    - 持久化记录（JSON）
    - 读取/写入 ConfigManager（提醒设置与预设）

    说明：这里仍然是“过渡期 facade”，等后续拆 ports 后可以进一步瘦身。
    """

    running_state_changed = pyqtSignal(bool)

    DEFAULT_REMINDER_SETTINGS = {
        "timer_end_seconds": None,
        "timer_remind_interval_seconds": 0,
        "timer_pause_after_remind_seconds": 0,
    }

    def __init__(self, log_path: Optional[str] = None, config_manager: Optional[object] = None, notifier: Optional[Callable[..., Any]] = None):
        super().__init__()
        self.config_manager = config_manager
        self.notifier = notifier

        self.log_path = log_path or os.path.join("config", "timer_log.json")
        self.log_repo = TimerLogRepository(self.log_path)
        self.settings_repo = TimerSettingsRepository(self.config_manager)

        self.service = TimerService(settings=self.settings_repo.load_settings())
        self.last_elapsed_seconds = 0.0

        # tick 定时器（Qt）
        self._tick_timer = QTimer()
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._on_tick)
        self._tick_timer.start()

    def __del__(self):
        self.shutdown()

    # ---- 外部依赖 ----
    def set_notifier(self, notifier: Callable[..., Any]) -> None:
        self.notifier = notifier

    # ---- 查询 ----
    def is_running(self) -> bool:
        return self.service.is_running()

    def is_paused(self) -> bool:
        return self.service.is_paused()

    def get_elapsed_seconds(self) -> float:
        return self.service.get_elapsed_seconds()

    def get_display_time(self):
        return self.service.get_display_time()

    def get_overlay_context(self):
        return self.service.get_overlay_context()

    # ---- 控制 ----
    def toggle(self) -> bool:
        result = self.service.toggle()
        self.running_state_changed.emit(self.is_running())
        return result

    def start(self) -> None:
        self.service.start()
        self.running_state_changed.emit(True)

    def pause(self) -> None:
        self.service.pause()
        self.running_state_changed.emit(False)

    def resume(self) -> None:
        self.service.resume()
        self.running_state_changed.emit(True)

    def stop_and_persist(self) -> None:
        if not self.is_running() and not self.is_paused():
            return
        # 结束：先暂停取数，再持久化，再 reset
        self.service.pause()
        self.last_elapsed_seconds = self.service.get_elapsed_seconds()
        self._persist_record()
        self.reset()

    def reset(self) -> None:
        self.service.reset()
        self.last_elapsed_seconds = 0.0
        self.running_state_changed.emit(False)

    # ---- 提醒设置（供 UI 窗口使用）----
    def update_reminder_settings(self, end_seconds, remind_interval_seconds, pause_after_remind_seconds):
        safe_end = end_seconds if (end_seconds is None or int(end_seconds) > 0) else None
        settings = ReminderSettings(
            end_seconds=safe_end,
            remind_interval_seconds=max(0, int(remind_interval_seconds or 0)),
            pause_after_remind_seconds=max(0, int(pause_after_remind_seconds or 0)),
        )
        self.service.set_settings(settings)
        self.settings_repo.save_settings(settings)

    def get_reminder_settings(self):
        s = self.service.get_settings()
        return {
            "timer_end_seconds": s.end_seconds,
            "timer_remind_interval_seconds": int(s.remind_interval_seconds),
            "timer_pause_after_remind_seconds": int(s.pause_after_remind_seconds),
        }

    # ---- 预设（供 UI 窗口使用）----
    def get_presets(self):
        return list(self.settings_repo.list_presets())

    def save_preset(self, name, preset_data):
        self.settings_repo.save_preset(name, preset_data or {})

    def delete_preset(self, name):
        self.settings_repo.delete_preset(name)

    def load_preset(self, name):
        return self.settings_repo.load_preset(name)

    # ---- 内部 tick ----
    def _on_tick(self):
        result: TickResult = self.service.tick()
        if result.notify_title and result.notify_message:
            self._notify(result.notify_title, result.notify_message)

        if result.should_stop_and_persist:
            self.stop_and_persist()

    def _notify(self, title, message):
        if callable(self.notifier):
            try:
                self.notifier(title, message)
                return
            except Exception:
                logger.exception("Timer notifier failed")
        print(f"[{title}]: {message}")

    def _persist_record(self):
        record = {
            "end_at": datetime.datetime.now().isoformat(),
            "elapsed_seconds": int(self.last_elapsed_seconds),
            "elapsed_hms": self.service.get_formatted_string(),
        }
        self.log_repo.append(record)

    def shutdown(self):
        try:
            if self._tick_timer.isActive():
                self._tick_timer.stop()
        except Exception:
            logger.exception("TimerFacadeQt shutdown failed")

    # 说明：Timer 的配置读写已统一下沉到 `src/storage/timer_settings_repository.py`


__all__ = ["TimerFacadeQt"]


