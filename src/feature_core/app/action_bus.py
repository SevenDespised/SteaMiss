from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from src.feature_core.app.actions import Action


Handler = Callable[..., Any]


logger = logging.getLogger(__name__)


@dataclass
class ActionBus:
    """
    动作总线（纯 Python，无 Qt）：
    - 顶层注册 Action -> handler
    - UI/Menu/Window 仅负责触发 Action，不直接依赖具体业务对象
    """

    _handlers: Dict[Action, Handler]
    _hooks: Dict[Action, list[Handler]]
    _on_error: Optional[Callable[[Exception, Action, dict], None]] = None

    def __init__(self) -> None:
        self._handlers = {}
        self._hooks = {}
        self._on_error = None

    def set_error_handler(self, fn: Callable[[Exception, Action, dict], None]) -> None:
        self._on_error = fn

    def register(self, action: Action, handler: Handler) -> None:
        self._handlers[action] = handler

    def register_hook(self, action: Action, hook: Handler) -> None:
        """注册钩子，在 execute 之后执行，不影响返回值"""
        if action not in self._hooks:
            self._hooks[action] = []
        self._hooks[action].append(hook)

    def _sanitize_kwargs(self, kwargs: dict) -> dict:
        redacted_keys = {
            "api_key",
            "steam_api_key",
            "llm_api_key",
            "authorization",
            "Authorization",
            "token",
            "access_token",
        }
        out: dict = {}
        for k, v in (kwargs or {}).items():
            if str(k) in redacted_keys:
                out[k] = "***"
            else:
                out[k] = v
        return out

    def execute(self, action: Action, **kwargs: Any) -> Any:
        handler = self._handlers.get(action)
        if not handler:
            raise KeyError(f"Unknown action: {action}")

        try:
            result = handler(**kwargs)
            # 执行钩子
            if action in self._hooks:
                for hook in self._hooks[action]:
                    try:
                        hook(**kwargs)
                    except Exception:
                        logger.exception(
                            "Action hook failed: %s",
                            action.value,
                            extra={"action": action.value, "kwargs": self._sanitize_kwargs(dict(kwargs))},
                        )
            return result
        except Exception as e:
            logger.exception(
                "Action failed: %s",
                action.value,
                extra={"action": action.value, "kwargs": self._sanitize_kwargs(dict(kwargs))},
            )
            if self._on_error:
                try:
                    self._on_error(e, action, dict(kwargs))
                except Exception:
                    logger.exception(
                        "Action on_error handler failed: %s",
                        action.value,
                        extra={"action": action.value, "kwargs": self._sanitize_kwargs(dict(kwargs))},
                    )
            # UI 场景下不希望异常冒泡导致崩溃；错误由 on_error 回调统一处理。
            return None


__all__ = ["ActionBus"]


