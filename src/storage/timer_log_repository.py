from __future__ import annotations

import json
import os
from typing import Any, Dict, List


class TimerLogRepository:
    """
    计时记录持久化（JSON）。
    仅负责追加写入，不承载业务规则。
    """

    def __init__(self, log_path: str) -> None:
        self.log_path = log_path

    def append(self, record: Dict[str, Any]) -> None:
        data: List[Dict[str, Any]] = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, list):
                    data = loaded
            except Exception:
                data = []

        data.append(record)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


__all__ = ["TimerLogRepository"]


