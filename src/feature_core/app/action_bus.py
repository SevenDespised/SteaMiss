from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from src.feature_core.app.actions import Action


Handler = Callable[..., Any]


@dataclass
class ActionBus:
    """
    动作总线（纯 Python，无 Qt）：
    - 顶层注册 Action -> handler
    - UI/Menu/Window 仅负责触发 Action，不直接依赖具体业务对象
    """

    _handlers: Dict[Action, Handler]
    _on_error: Optional[Callable[[Exception, Action, dict], None]] = None

    def __init__(self) -> None:
        self._handlers = {}
        self._on_error = None

    def set_error_handler(self, fn: Callable[[Exception, Action, dict], None]) -> None:
        self._on_error = fn

    def register(self, action: Action, handler: Handler) -> None:
        self._handlers[action] = handler

    def execute(self, action: Action, **kwargs: Any) -> Any:
        handler = self._handlers.get(action)
        if not handler:
            raise KeyError(f"Unknown action: {action}")

        try:
            return handler(**kwargs)
        except Exception as e:
            if self._on_error:
                try:
                    self._on_error(e, action, dict(kwargs))
                except Exception:
                    pass
            # UI 场景下不希望异常冒泡导致崩溃；错误由 on_error 回调统一处理。
            return None


__all__ = ["ActionBus"]


