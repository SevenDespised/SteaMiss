from __future__ import annotations

import json
import os
from typing import Any, Optional

from PyQt6.QtCore import QObject, pyqtSignal


class NewsRepository(QObject):
    """新闻数据持久化层：保存每日新闻缓存与缓存日期。"""

    error_occurred = pyqtSignal(str)

    def __init__(self, data_file: str = "config/news_data.json"):
        super().__init__()
        self.data_file = data_file

    def load_data(self) -> dict[str, Any]:
        """加载本地新闻缓存。返回 dict：{"date": "YYYY-MM-DD", "items": [...]}。"""
        if not os.path.exists(self.data_file):
            return {}

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
        except Exception as e:
            msg = f"Failed to load local news data: {e}"
            print(msg)
            self.error_occurred.emit(msg)
            return {}

    def save_data(self, data: dict[str, Any]) -> None:
        """保存新闻缓存数据到本地。"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved news data to {self.data_file}")
        except Exception as e:
            msg = f"Failed to save local news data: {e}"
            print(msg)
            self.error_occurred.emit(msg)

    def load_cached_items(self) -> tuple[Optional[str], list[dict[str, Any]]]:
        data = self.load_data() or {}
        date_str = data.get("date") if isinstance(data, dict) else None
        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, list):
            items = []
        return (date_str if isinstance(date_str, str) else None, items)

    def save_cached_items(self, date_str: str, items: list[dict[str, Any]]) -> None:
        self.save_data({"date": date_str, "items": items})


__all__ = ["NewsRepository"]
