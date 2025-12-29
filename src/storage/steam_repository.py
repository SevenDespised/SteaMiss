from __future__ import annotations

import json
import os
import logging
from typing import Any, Callable, Optional


logger = logging.getLogger(__name__)


class SteamRepository:
    """Steam 数据持久化层（纯 Python）"""

    def __init__(self, data_file: str = "config/steam_data.json") -> None:
        self.data_file = data_file
        self._on_error: Optional[Callable[[str], Any]] = None

    def set_error_handler(self, fn: Callable[[str], Any]) -> None:
        self._on_error = fn

    def load_data(self):
        """加载本地缓存数据"""
        cache = {}
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info("Loaded local steam data from %s", self.data_file)
            except Exception as e:
                msg = f"Failed to load local steam data: {e}"
                logger.exception("%s", msg)
                if callable(self._on_error):
                    try:
                        self._on_error(msg)
                    except Exception:
                        logger.exception("SteamRepository error handler failed")
        return cache

    def save_data(self, data):
        """保存缓存数据到本地"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Saved steam data to %s", self.data_file)
        except Exception as e:
            msg = f"Failed to save local steam data: {e}"
            logger.exception("%s", msg)
            if callable(self._on_error):
                try:
                    self._on_error(msg)
                except Exception:
                    logger.exception("SteamRepository error handler failed")
