from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class WindowContext:
    """
    窗口依赖上下文（轻量 DI）。

    说明：
    - 由 `src/application.py:SteaMissApp` 统一创建各类 Manager/Handler 并注入到这里；
    - Binder 通过该上下文拿到依赖，避免在 UI/窗口模块内到处 import 业务对象。
    """

    steam_manager: object
    config_manager: object
    timer_handler: object
    news_manager: object = None
    epic_manager: object = None
    prompt_manager: object = None
    navigate: Optional[Callable[[str], None]] = None


__all__ = ["WindowContext"]


