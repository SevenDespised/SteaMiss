from __future__ import annotations

from enum import Enum


class Action(str, Enum):
    """
    应用动作枚举：统一 action_key，避免字符串散落。
    """

    # System
    OPEN_PATH = "open_path"
    OPEN_URL = "open_url"
    EXIT = "exit"

    # Steam
    LAUNCH_GAME = "launch_game"
    OPEN_STEAM_PAGE = "open_steam_page"

    # Timer
    TOGGLE_TIMER = "toggle_timer"
    PAUSE_TIMER = "pause_timer"
    RESUME_TIMER = "resume_timer"
    STOP_TIMER = "stop_timer"

    # UI intents (由业务触发 UI 行为)
    OPEN_WINDOW = "open_window"
    SAY_HELLO = "say_hello"
    HIDE_PET = "hide_pet"
    TOGGLE_TOPMOST = "toggle_topmost"


__all__ = ["Action"]


