from __future__ import annotations

from typing import Any, Callable, Optional, Protocol


class SignalLike(Protocol):
    def connect(self, slot: Callable[[Any], Any]) -> None: ...


class SteamTaskServicePort(Protocol):
    """Steam 异步任务调度端口（最小接口）。"""

    task_finished: SignalLike

    def start_task(
        self,
        key: str,
        sid: str,
        task_type: str,
        extra_data: Any = None,
        steam_id: Optional[str] = None,
    ) -> None: ...


class SteamRepositoryPort(Protocol):
    """Steam 缓存仓库端口（最小接口）。"""

    def set_error_handler(self, fn: Callable[[str], Any]) -> None: ...

    def load_data(self) -> dict: ...

    def save_data(self, data: dict) -> None: ...


__all__ = ["SignalLike", "SteamTaskServicePort", "SteamRepositoryPort"]
