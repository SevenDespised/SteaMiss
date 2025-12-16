from __future__ import annotations

from typing import Any, List, Optional

from src.feature_core.domain.steam_account_models import SteamAccountPolicy


class SteamAccountService:
    """
    Steam 账号策略子域（纯 Python）：
    - 只负责从 ConfigManager 解析出账号策略（主号/子号/去重）

    边界：
    - 不做 games 聚合、recent/search、datasets 组织
    - 不做 profile/price/wishlist/achievement 的 cache 更新
    """

    def build_policy(self, config_manager: object) -> SteamAccountPolicy:
        get = getattr(config_manager, "get", lambda *_: None)

        api_key = get("steam_api_key")
        primary_id = get("steam_id")

        raw_alt_ids = get("steam_alt_ids", [])
        alt_ids: List[str] = []
        if isinstance(raw_alt_ids, list):
            for sid in raw_alt_ids:
                if sid:
                    alt_ids.append(sid)

        account_ids: List[str] = []
        if primary_id:
            account_ids.append(primary_id)
        for sid in alt_ids:
            if sid and sid not in account_ids:
                account_ids.append(sid)

        return SteamAccountPolicy(
            api_key=api_key if api_key else None,
            primary_id=primary_id if primary_id else None,
            alt_ids=alt_ids,
            account_ids=account_ids,
        )

    def get_primary_credentials(self, config_manager: object) -> tuple[Optional[str], Optional[str]]:
        policy = self.build_policy(config_manager)
        return policy.api_key, policy.primary_id

    def get_all_account_ids(self, config_manager: object) -> List[str]:
        return self.build_policy(config_manager).account_ids


__all__ = ["SteamAccountService"]


