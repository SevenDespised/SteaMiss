from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Optional

from src.feature_core.domain.timer_models import ReminderSettings
from src.feature_core.timer_support.timer_logic import GameTimer


@dataclass(frozen=True)
class TickResult:
    """
    tick() 的结果：纯业务事件汇总，外层（Qt facade）决定如何持久化/通知/UI 更新。
    """

    should_stop_and_persist: bool = False
    notify_title: Optional[str] = None
    notify_message: Optional[str] = None


class TimerService:
    """
    纯业务计时服务（不依赖 Qt）。
    - 持有 GameTimer
    - 维护提醒/结束/自动暂停&自动恢复的业务状态
    """

    def __init__(self, settings: Optional[ReminderSettings] = None) -> None:
        self.timer = GameTimer()
        self.settings = settings or ReminderSettings()

        self._next_remind_at: Optional[float] = None
        self._auto_paused: bool = False
        self._auto_resume_at_ts: Optional[float] = None

    # ---- 状态 ----
    def is_running(self) -> bool:
        return bool(self.timer.is_running)

    def is_paused(self) -> bool:
        # 既不是 running，又有 accumulated_time，说明是暂停状态
        return (not self.timer.is_running) and (self.timer.accumulated_time > 0)

    # ---- 控制 ----
    def toggle(self) -> bool:
        if self.is_running():
            self.timer.pause()
            return False
        self.start()
        return True

    def start(self) -> None:
        self._auto_paused = False
        self._auto_resume_at_ts = None
        self.timer.start()
        self._sync_next_reminder()

    def pause(self) -> None:
        self._auto_paused = False
        self._auto_resume_at_ts = None
        self.timer.pause()

    def resume(self) -> None:
        self._auto_paused = False
        self._auto_resume_at_ts = None
        self.timer.start()
        self._sync_next_reminder()

    def reset(self) -> None:
        self.timer.reset()
        self._next_remind_at = None
        self._auto_paused = False
        self._auto_resume_at_ts = None

    # ---- 数据 ----
    def get_elapsed_seconds(self) -> float:
        return float(self.timer.get_total_seconds())

    def get_display_time(self):
        return self.timer.get_time_parts()

    def get_formatted_string(self) -> str:
        return self.timer.get_formatted_string()

    def get_overlay_context(self):
        running = self.is_running()
        elapsed = self.get_elapsed_seconds()
        if (not running) and elapsed <= 0:
            return None
        h, m, s = self.get_display_time()
        return {"h": h, "m": m, "s": s, "is_running": running}

    # ---- 设置 ----
    def set_settings(self, settings: ReminderSettings) -> None:
        self.settings = settings
        self._sync_next_reminder()

    def get_settings(self) -> ReminderSettings:
        return self.settings

    # ---- Tick ----
    def tick(self) -> TickResult:
        """
        每秒调用一次即可（由 Qt facade 调度）。
        """
        running = self.is_running()
        paused = self.is_paused()
        if not running and not paused:
            return TickResult()

        now_ts = time.time()

        # 自动恢复：仅针对“提醒后自动暂停”的场景
        if (not running) and self._auto_paused and self._auto_resume_at_ts is not None and now_ts >= self._auto_resume_at_ts:
            # 恢复
            self.timer.start()
            self._auto_paused = False
            self._auto_resume_at_ts = None
            self._sync_next_reminder()
            return TickResult()

        elapsed = self.get_elapsed_seconds()

        # 结束条件：只在运行中检查
        end_seconds = self.settings.end_seconds
        if running and end_seconds is not None and elapsed >= float(end_seconds):
            return TickResult(
                should_stop_and_persist=True,
                notify_title="计时结束",
                notify_message="已达到设定的结束时间。",
            )

        # 暂停状态不做提醒（避免重复）
        if not running:
            return TickResult()

        interval = int(self.settings.remind_interval_seconds or 0)
        if interval <= 0:
            return TickResult()

        if self._next_remind_at is None:
            self._sync_next_reminder()

        if self._next_remind_at is not None and elapsed >= self._next_remind_at:
            msg = f"已计时 {self.get_formatted_string()}。"
            # 计算下一次提醒：保持“固定间隔”推进
            self._next_remind_at = elapsed + interval

            pause_seconds = int(self.settings.pause_after_remind_seconds or 0)
            if pause_seconds > 0 and self.is_running():
                self._auto_paused = True
                self.timer.pause()
                self._auto_resume_at_ts = now_ts + float(pause_seconds)

            return TickResult(should_stop_and_persist=False, notify_title="计时提醒", notify_message=msg)

        return TickResult()

    def _sync_next_reminder(self) -> None:
        interval = int(self.settings.remind_interval_seconds or 0)
        if interval <= 0:
            self._next_remind_at = None
            return
        elapsed = self.get_elapsed_seconds()
        self._next_remind_at = (math.floor(elapsed / interval) + 1) * interval


__all__ = ["TimerService", "TickResult"]


