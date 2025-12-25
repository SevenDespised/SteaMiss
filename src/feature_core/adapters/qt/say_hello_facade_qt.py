from __future__ import annotations

import threading
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

    def say_hello(self, **kwargs) -> None:
        _ = kwargs

        fallback = self._pet_service.get_say_hello_fallback_text()
        prompt = self._pet_service.build_say_hello_prompt(self._prompt_manager, self._steam_manager)

        def _run() -> None:
            try:
                if not isinstance(prompt, str) or not prompt.strip():
                    self._ui_intents.say_hello.emit(fallback)
                    return

                content: Optional[str] = self._llm_service.chat_completion(
                    [{"role": "user", "content": prompt}]
                )
                if isinstance(content, str) and content.strip():
                    self._ui_intents.say_hello.emit(content.strip())
                else:
                    self._ui_intents.say_hello.emit(fallback)
            except Exception:
                self._ui_intents.say_hello.emit(fallback)

        threading.Thread(target=_run, daemon=True).start()


__all__ = ["SayHelloFacadeQt"]
