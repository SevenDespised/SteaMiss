from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LaunchPlan:
    """
    启动计划（纯数据）：
    - primary_uri: 优先尝试打开的 URI（通常是 steam://）
    - fallback_url: 失败时可回退打开的网页（可为空）
    """

    primary_uri: str
    fallback_url: Optional[str] = None


class SteamLauncherService:
    """
    Steam 启动/跳转用例（纯 Python，不依赖 Qt/OS）：
    - 只负责把输入（appid/page_type）转换为可执行的 URI/URL 计划
    - 实际“怎么打开”由 Qt facade 决定
    """

    STEAM_COMMANDS = {
        "store": "steam://store",
        "community": "steam://url/CommunityHome",
        "library": "steam://nav/games",
        "workshop": "steam://url/SteamWorkshop",
        "profile": "steam://url/SteamIDEditPage",
        "downloads": "steam://nav/downloads",
        "settings": "steam://settings/",
    }

    WEB_URLS = {
        "store": "https://store.steampowered.com/",
        "community": "https://steamcommunity.com/",
        "library": "https://steamcommunity.com/my/games",
        "workshop": "https://steamcommunity.com/workshop/",
        "profile": "https://steamcommunity.com/my/profile/edit",
        "downloads": "https://store.steampowered.com/account/",
        "settings": "https://store.steampowered.com/account/",
    }

    def build_launch_game(self, appid: object) -> Optional[LaunchPlan]:
        if not appid:
            return None
        return LaunchPlan(primary_uri=f"steam://run/{appid}", fallback_url=None)

    def build_open_page(self, page_type: str) -> Optional[LaunchPlan]:
        page_type = (page_type or "").strip()
        if not page_type:
            return None
        cmd = self.STEAM_COMMANDS.get(page_type)
        url = self.WEB_URLS.get(page_type)
        if cmd:
            return LaunchPlan(primary_uri=cmd, fallback_url=url)
        if url:
            # 没有 steam:// 命令时，直接网页作为 primary
            return LaunchPlan(primary_uri=url, fallback_url=None)
        return None


__all__ = ["LaunchPlan", "SteamLauncherService"]
