from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ReminderSettings:
    """
    计时提醒设置（纯数据）。
    - end_seconds: 达到该累计时长后结束；None 表示不结束
    - remind_interval_seconds: 提醒间隔；0 表示不提醒
    - pause_after_remind_seconds: 提醒后自动暂停时长；0 表示不暂停
    """

    end_seconds: Optional[int] = None
    remind_interval_seconds: int = 0
    pause_after_remind_seconds: int = 0


__all__ = ["ReminderSettings"]


