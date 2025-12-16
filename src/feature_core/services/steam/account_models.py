from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class SteamAccountPolicy:
    """
    Steam 账号策略（纯数据）：
    - api_key: Steam Web API Key
    - primary_id: 主账号 steam_id
    - alt_ids: 子账号 steam_id 列表（保持配置顺序）
    - account_ids: 实际需要抓取的账号列表（primary + alt 去重后）
    """

    api_key: Optional[str]
    primary_id: Optional[str]
    alt_ids: List[str]
    account_ids: List[str]


__all__ = ["SteamAccountPolicy"]


