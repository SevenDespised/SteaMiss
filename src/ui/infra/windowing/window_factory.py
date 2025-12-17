from __future__ import annotations

from typing import Callable, Optional

from src.ui.infra.windowing.build_registry import build_window_registry
from src.ui.infra.windowing.context import WindowContext


class WindowFactory:
    """
    窗口工厂：创建窗口并执行 Binder 接线。
    """

    def __init__(self, steam_manager, config_manager, timer_handler):
        # 保存基础依赖（便于注入 navigator 时重建 ctx）
        self._steam_manager = steam_manager
        self._config_manager = config_manager
        self._timer_handler = timer_handler

        self._ctx = WindowContext(
            steam_manager=self._steam_manager,
            config_manager=self._config_manager,
            timer_handler=self._timer_handler,
            navigate=None,
        )
        self._registry = build_window_registry()

    def set_navigator(self, navigate: Callable[[str], None]) -> None:
        """
        注入窗口导航回调（用于 Binder 内部触发“开窗”意图）。
        @param navigate: callable(window_name: str) -> None
        """
        self._ctx = WindowContext(
            steam_manager=self._steam_manager,
            config_manager=self._config_manager,
            timer_handler=self._timer_handler,
            navigate=navigate,
        )

    def create_window(self, window_name: str, parent: Optional[object] = None) -> Optional[object]:
        """
        通用创建入口：通过 registry 查表创建窗口并执行 binder 绑定。
        @param window_name: window_name（例如 'stats'/'all_games'）
        @param parent: Qt parent（可选）
        """
        spec = self._registry.get(window_name)
        if not spec:
            return None

        view = spec.create(self._ctx, parent)
        if spec.binder:
            spec.binder.bind(view, self._ctx)
        return view


__all__ = ["WindowFactory"]


