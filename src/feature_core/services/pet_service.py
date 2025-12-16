from __future__ import annotations

from typing import Optional


class PetService:
    """
    宠物用例/业务服务（纯 Python，不依赖 Qt）。

    当前阶段：只提供“打招呼文案”的读取。
    后续可在这里逐步扩展：
    - 宠物数值计算（可下沉到 domain）
    - 行为决策/行为队列（services）
    - 与 UI 的交互通过 UiIntentsQt / PetFacadeQt 完成
    """

    def __init__(self, config_manager: Optional[object] = None) -> None:
        self.config_manager = config_manager

    def get_say_hello_content(self) -> str:
        """获取“打招呼”文案（来自配置）。"""
        if not self.config_manager:
            return "你好！"
        try:
            return self.config_manager.get("say_hello_content", "你好！")
        except Exception:
            return "你好！"


__all__ = ["PetService"]


