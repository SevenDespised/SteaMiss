from __future__ import annotations

import os
from typing import Optional

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication

from src.feature_core.services.system_service import SystemService


class SystemFacadeQt:
    """
    Qt/系统适配入口：SystemFacadeQt

    职责：
    - 委托 SystemService 执行系统行为（打开路径/URL）
    - 退出应用（QApplication.quit）

    说明：这类代码属于 adapters/qt（依赖 PyQt6 或 OS API），不应放在 services/domain。
    """

    def __init__(self, config_manager: Optional[object] = None) -> None:
        self.config_manager = config_manager
        self.service = SystemService(config_manager=config_manager)

    def open_explorer(self, path: Optional[str] = None, **_: object) -> None:
        """
        打开资源管理器并定位到指定路径；未传入时使用配置的 explorer_paths[0]。
        """
        self.service.open_explorer(path=path)

    def open_url(self, url: Optional[str] = None, **_: object) -> None:
        """打开 URL。"""
        self.service.open_url(url=url)

    def open_uri(self, uri: Optional[str] = None, fallback_url: Optional[str] = None, **_: object) -> None:
        """打开 URI（例如 steam:// 或 http(s)://）。

        优先尝试 os.startfile(uri)；失败且提供 fallback_url 时，尝试用 Qt 打开网页。
        """
        if not uri:
            return
        try:
            os.startfile(uri)
            return
        except Exception as e:
            if fallback_url:
                try:
                    QDesktopServices.openUrl(QUrl(fallback_url))
                    return
                except Exception:
                    pass
            raise Exception(f"Failed to open URI {uri}: {e}")

    def exit_app(self, **_: object) -> None:
        """退出应用。"""
        QApplication.instance().quit()


__all__ = ["SystemFacadeQt"]


