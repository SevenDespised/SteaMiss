from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal


class UiIntentsQt(QObject):
    """
    UI 意图（Qt 信号集合）：
    业务/动作触发“想让 UI 做什么”，由 application.py 负责接线到具体 UI 实现。
    """

    open_window = pyqtSignal(str)
    say_hello = pyqtSignal(str)
    # 流式输出：开始/增量/结束（用于气泡逐步更新文本）
    say_hello_stream_started = pyqtSignal(str)  # request_id
    say_hello_stream_delta = pyqtSignal(str, str)  # request_id, delta
    say_hello_stream_done = pyqtSignal(str)  # request_id
    activate_pet = pyqtSignal()
    hide_pet = pyqtSignal()
    toggle_topmost = pyqtSignal()
    error = pyqtSignal(str)
    notification = pyqtSignal(str, str)  # title, message


__all__ = ["UiIntentsQt"]


