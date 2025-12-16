from __future__ import annotations

from typing import Any, Dict, Optional


class SteamGamesService:
    """
    Steam Games 用例协调器（纯 Python）。

    说明：
    - 当前阶段尚无“多 service 协同”的复杂用例，因此不在此处组合 query/dataset/aggregation 等子域 service；
    - 现有逻辑已分别下沉到：
      - `SteamAccountService`（账号策略）
      - `SteamQueryService`（recent/search/primary cache）
      - `SteamDatasetService`（datasets/tab 组织）
      - `SteamGamesAggregationService`（聚合结果写回 cache）
      - profile/price/wishlist/achievement 子域 services（各自 cache 更新）
    - 当未来出现需要协同多个子域的用例（例如“刷新 games 后按需补齐价格/成就并生成 UI 视图”），
      再把该协同流程上浮到本类中，避免上浮到 Qt 层。
    """

    def plan_future_orchestration(self, _: Optional[object] = None) -> Dict[str, Any]:
        """
        预留：未来协同用例入口（占位）。
        当前不使用。
        """
        return {}


__all__ = ["SteamGamesService"]



