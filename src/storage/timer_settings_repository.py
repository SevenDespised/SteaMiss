from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.feature_core.domain.timer_models import ReminderSettings


class TimerSettingsRepository:
    """
    Timer 设置仓库：
    - 统一读写 ConfigManager 内的 `timer_reminder` 与 `timer_reminder_presets`
    - 不承载“提醒/结束/暂停策略”的业务规则（那些在 TimerService）
    """

    DEFAULT = {
        "timer_end_seconds": None,
        "timer_remind_interval_seconds": 0,
        "timer_pause_after_remind_seconds": 0,
    }

    def __init__(self, config_manager: Optional[object]) -> None:
        self.config_manager = config_manager

    def load_settings(self) -> ReminderSettings:
        cfg = self.config_manager
        raw: Dict[str, Any] = {}
        if cfg:
            stored = cfg.get("timer_reminder", {})
            if isinstance(stored, dict):
                raw = stored

        end_seconds = raw.get("timer_end_seconds", self.DEFAULT["timer_end_seconds"])
        if end_seconds is not None:
            try:
                end_seconds = int(end_seconds)
            except Exception:
                end_seconds = None
            if end_seconds is not None and end_seconds <= 0:
                end_seconds = None

        remind_interval = raw.get("timer_remind_interval_seconds", self.DEFAULT["timer_remind_interval_seconds"])
        pause_after = raw.get("timer_pause_after_remind_seconds", self.DEFAULT["timer_pause_after_remind_seconds"])

        return ReminderSettings(
            end_seconds=end_seconds,
            remind_interval_seconds=max(0, int(remind_interval or 0)),
            pause_after_remind_seconds=max(0, int(pause_after or 0)),
        )

    def save_settings(self, settings: ReminderSettings) -> None:
        if not self.config_manager:
            return
        self.config_manager.set(
            "timer_reminder",
            {
                "timer_end_seconds": settings.end_seconds,
                "timer_remind_interval_seconds": int(settings.remind_interval_seconds),
                "timer_pause_after_remind_seconds": int(settings.pause_after_remind_seconds),
            },
        )

    # ---- presets ----
    def list_presets(self) -> List[dict]:
        if self.config_manager:
            presets = self.config_manager.get("timer_reminder_presets", [])
            if isinstance(presets, list):
                return presets
        return []

    def load_preset(self, name: str) -> Optional[dict]:
        if not name:
            return None
        for p in self.list_presets():
            if p.get("name") == name:
                return dict(p)
        return None

    def save_preset(self, name: str, preset_data: dict) -> None:
        if not self.config_manager or not name:
            return
        presets = [p for p in self.list_presets() if p.get("name") != name]
        presets.append({"name": name, **(preset_data or {})})
        self.config_manager.set("timer_reminder_presets", presets)

    def delete_preset(self, name: str) -> None:
        if not self.config_manager or not name:
            return
        presets = [p for p in self.list_presets() if p.get("name") != name]
        self.config_manager.set("timer_reminder_presets", presets)


__all__ = ["TimerSettingsRepository"]


