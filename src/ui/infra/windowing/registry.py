from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Protocol

from src.ui.infra.windowing.context import WindowContext


class WindowBinder(Protocol):
    """
    窗口绑定器协议：负责把 View 的信号与业务层连接，并做必要的首次刷新。
    """

    def bind(self, view: object, ctx: WindowContext) -> None:
        """
        @param view: 具体窗口实例（QWidget/QDialog 等）
        @param ctx: WindowContext（包含 steam/config/timer/navigate）
        """


@dataclass(frozen=True)
class WindowSpec:
    """
    Window 注册描述。
    - create: 只负责创建窗口（惰性 import 放在这里，避免启动时导入大量 UI 模块）
    - binder: 负责信号绑定与首次刷新
    """

    create: Callable[[WindowContext, Optional[object]], object]
    binder: Optional[WindowBinder] = None


class WindowRegistry:
    """
    Window 注册表：window_name -> WindowSpec
    """

    def __init__(self) -> None:
        self._specs: Dict[str, WindowSpec] = {}

    def register(self, name: str, spec: WindowSpec) -> None:
        self._specs[name] = spec

    def get(self, name: str) -> Optional[WindowSpec]:
        return self._specs.get(name)


__all__ = ["WindowBinder", "WindowRegistry", "WindowSpec"]


