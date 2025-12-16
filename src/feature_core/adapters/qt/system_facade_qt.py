from __future__ import annotations

from typing import Optional

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

    def exit_app(self, **_: object) -> None:
        """退出应用。"""
        QApplication.instance().quit()


__all__ = ["SystemFacadeQt"]


