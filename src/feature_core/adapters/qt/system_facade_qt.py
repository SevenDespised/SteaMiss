from __future__ import annotations

import logging
import os
import winreg
from typing import Optional

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication

from src.feature_core.services.system_service import SystemService


logger = logging.getLogger(__name__)


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

    def _is_steam_installed(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            return bool(path and os.path.exists(path))
        except Exception:
            return False

    def open_uri(self, uri: Optional[str] = None, fallback_url: Optional[str] = None, **_: object) -> None:
        """打开 URI（例如 steam:// 或 http(s)://）。

        优先尝试 os.startfile(uri)；失败且提供 fallback_url 时，尝试用 Qt 打开网页。
        """
        if not uri:
            return

        should_try_startfile = True
        # 针对 steam:// 协议：预先检查 Steam 是否安装，避免 Windows 尝试打开应用商店
        if uri.startswith("steam://") and not self._is_steam_installed():
            should_try_startfile = False
            logger.info("Steam not installed (registry check)")

        startfile_error = None
        if should_try_startfile:
            try:
                os.startfile(uri)
                return
            except Exception as e:
                startfile_error = e
                logger.warning("os.startfile failed for %s: %s", uri, e)

        if fallback_url:
            try:
                QDesktopServices.openUrl(QUrl(fallback_url))
                return
            except Exception:
                logger.exception("Failed to open fallback URL: %s", fallback_url)

        if not should_try_startfile:
            raise Exception(f"Steam not installed, cannot open URI: {uri}")
        raise Exception(f"Failed to open URI {uri}: {startfile_error}")

    def exit_app(self, **_: object) -> None:
        """退出应用。"""
        QApplication.instance().quit()


__all__ = ["SystemFacadeQt"]
