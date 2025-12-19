from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal


class UiIntentsQt(QObject):
    """
    UI 意图（Qt 信号集合）：
    业务/动作触发“想让 UI 做什么”，由 application.py 负责接线到具体 UI 实现。
    """

    open_window = pyqtSignal(str)
    say_hello = pyqtSignal(str)
    activate_pet = pyqtSignal()
    hide_pet = pyqtSignal()
    toggle_topmost = pyqtSignal()
    error = pyqtSignal(str)


__all__ = ["UiIntentsQt"]


