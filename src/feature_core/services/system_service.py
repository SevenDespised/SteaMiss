from __future__ import annotations

import os
import webbrowser
from typing import Optional


class SystemService:
    """
    系统用例/服务（纯 Python，不依赖 Qt）。

    职责：
    - 打开资源管理器路径（os.startfile）
    - 打开 URL（webbrowser）

    说明：
    - 这类能力属于“系统/IO”，放在 services 便于上层统一注入与替换；
    - 若未来需要更严格的分层，可将 os/webbrowser 进一步下沉到 adapters/os，再由本 service 组合。
    """

    def __init__(self, config_manager: Optional[object] = None) -> None:
        self.config_manager = config_manager

    def open_explorer(self, path: Optional[str] = None) -> None:
        """
        打开资源管理器并定位到指定路径；未传入时使用配置的 explorer_paths[0]。
        """
        if path is None:
            paths = []
            if self.config_manager:
                try:
                    paths = self.config_manager.get("explorer_paths", ["C:/"])
                except Exception:
                    paths = ["C:/"]
            else:
                paths = ["C:/"]
            path = (paths[0] if paths else "C:/") or "C:/"

        if not os.path.exists(path):
            raise Exception(f"Path not found: {path}")
        try:
            os.startfile(path)
        except Exception as e:
            raise Exception(f"Failed to open path {path}: {e}")

    def open_url(self, url: Optional[str] = None) -> None:
        """打开 URL。"""
        if not url:
            return
        try:
            webbrowser.open(url)
        except Exception as e:
            raise Exception(f"Failed to open URL {url}: {e}")


__all__ = ["SystemService"]


