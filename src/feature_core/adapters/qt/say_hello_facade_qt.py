from __future__ import annotations

import threading
import time
import uuid
from typing import Optional

from PyQt6.QtCore import QObject


class SayHelloFacadeQt(QObject):
    """Qt 边界：负责异步生成打招呼内容并驱动 UI。

    设计意图：
    - application.py 只负责组装/接线，不承载业务编排逻辑。
    - 业务侧（PetService）只负责构建 prompt 与回退值，不直接依赖 Qt。
    - 异步与 UI 信号 emit 属于 Qt 边界，集中在这里。
    """

    def __init__(
        self,
        *,
        ui_intents,
        pet_service,
        llm_service,
        prompt_manager,
        steam_manager,
    ) -> None:
        super().__init__()
        self._ui_intents = ui_intents
        self._pet_service = pet_service
        self._llm_service = llm_service
        self._prompt_manager = prompt_manager
        self._steam_manager = steam_manager
        self._active_request_id: Optional[str] = None

    def say_hello(self, **kwargs) -> None:
        _ = kwargs

        request_id = uuid.uuid4().hex
        self._active_request_id = request_id

        fallback = self._pet_service.get_say_hello_fallback_text()
        prompt = self._pet_service.build_say_hello_prompt(self._prompt_manager, self._steam_manager)

        # 通知 UI：开始流式
        self._ui_intents.say_hello_stream_started.emit(request_id)

        def _run() -> None:
            try:
                if not isinstance(prompt, str) or not prompt.strip():
                    self._ui_intents.say_hello_stream_delta.emit(request_id, fallback)
                    return

                # 轻量节流：累积一小段再发，避免 UI 每 token 重绘
                buffer = ""
                last_flush = time.monotonic()
                has_output = False

                for delta in self._llm_service.stream_chat_completion(
                    [{"role": "user", "content": prompt}]
                ):
                    # 取消：如果用户触发了新的 say_hello，请停止本次输出
                    if self._active_request_id != request_id:
                        return

                    if not isinstance(delta, str) or not delta:
                        continue

                    has_output = True
                    buffer += delta

                    now = time.monotonic()
                    if len(buffer) >= 20 or (now - last_flush) >= 0.05:
                        self._ui_intents.say_hello_stream_delta.emit(request_id, buffer)
                        buffer = ""
                        last_flush = now

                if self._active_request_id != request_id:
                    return

                if buffer:
                    self._ui_intents.say_hello_stream_delta.emit(request_id, buffer)

                if not has_output:
                    self._ui_intents.say_hello_stream_delta.emit(request_id, fallback)
            except Exception:
                if self._active_request_id != request_id:
                    return
                self._ui_intents.say_hello_stream_delta.emit(request_id, fallback)
            finally:
                if self._active_request_id == request_id:
                    self._ui_intents.say_hello_stream_done.emit(request_id)

        threading.Thread(target=_run, daemon=True).start()


__all__ = ["SayHelloFacadeQt"]
