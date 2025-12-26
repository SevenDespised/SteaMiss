from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

from src.feature_core.services.steam.games_aggregator import GamesAggregator
from src.feature_core.services.steam.games_aggregation_service import SteamGamesAggregationService
from src.feature_core.services.steam.profile_service import SteamProfileService
from src.feature_core.services.steam.price_service import SteamPriceService
from src.feature_core.services.steam.wishlist_service import SteamWishlistService
from src.feature_core.services.steam.achievement_service import SteamAchievementService


@dataclass(frozen=True)
class EmitPlayerSummary:
    payload: Any


@dataclass(frozen=True)
class EmitGamesStats:
    payload: Any


@dataclass(frozen=True)
class EmitStorePrices:
    payload: Any


@dataclass(frozen=True)
class EmitWishlist:
    payload: Any


@dataclass(frozen=True)
class EmitAchievements:
    payload: Any


@dataclass(frozen=True)
class EmitError:
    payload: Any


@dataclass(frozen=True)
class SaveStep:
    """一步操作：要求外层将 cache 持久化。"""

    reason: str


EmitStep = Union[
    EmitPlayerSummary,
    EmitGamesStats,
    EmitStorePrices,
    EmitWishlist,
    EmitAchievements,
    EmitError,
]


Step = Union[EmitStep, SaveStep]


@dataclass(frozen=True)
class ProcessOutcome:
    """处理 worker result 后的动作序列。

    为了保持现有行为，steps 顺序需要严格复刻原实现中：
    - 聚合 finalize 可能先触发 emit + save
    - 随后才 emit error（error 分支）
    - 正常分支最后可能还会发生一次 after_task save
    """

    steps: List[Step]


class SteamResultProcessor:
    """纯 Python 结果处理器
    """

    def __init__(
        self,
        *,
        cache: Dict[str, Any],
        games_aggregator: GamesAggregator,
        get_primary_id: Callable[[], Optional[str]],
        games_aggregation_service: SteamGamesAggregationService,
        profile_service: SteamProfileService,
        price_service: SteamPriceService,
        wishlist_service: SteamWishlistService,
        achievement_service: SteamAchievementService,
    ) -> None:
        self._cache = cache
        self._games_aggregator = games_aggregator
        self._get_primary_id = get_primary_id

        self._games_aggregation_service = games_aggregation_service
        self._profile_service = profile_service
        self._price_service = price_service
        self._wishlist_service = wishlist_service
        self._achievement_service = achievement_service

    def process(self, result: Dict[str, Any]) -> ProcessOutcome:
        steps: List[Step] = []

        if result.get("error"):
            # games_stats 目前走 profile_and_games；离线/失败时也要正确减少 pending，
            # 否则聚合器会一直卡在未完成状态。
            if result.get("type") in ("games", "profile_and_games") and self._games_aggregator:
                done = self._games_aggregator.mark_error()
                if done:
                    steps.extend(self._finalize_games_steps())

            steps.append(EmitError(result["error"]))
            return ProcessOutcome(steps=steps)

        task_type = result.get("type")
        data = result.get("data")
        if data is None:
            return ProcessOutcome(steps=[])

        if task_type == "summary":
            updates = self._profile_service.apply_summary(self._cache, data)
            summary_to_emit = updates.get("summary_to_emit")
            if summary_to_emit:
                steps.append(EmitPlayerSummary(summary_to_emit))

        elif task_type in ("games", "profile_and_games"):
            steam_id = result.get("steam_id")
            if task_type == "profile_and_games":
                games_data = data.get("games") if data else None
                summary_data = data.get("summary") if data else None
            else:
                games_data = data
                summary_data = None

            if self._games_aggregator:
                if games_data is None:
                    done = self._games_aggregator.mark_error()
                    if done:
                        steps.extend(self._finalize_games_steps())
                else:
                    done = self._games_aggregator.add_result(steam_id, games_data, summary_data)
                    if done:
                        steps.extend(self._finalize_games_steps())

        elif task_type == "store_prices":
            updates = self._price_service.apply_store_prices(self._cache, data)
            prices_to_emit = updates.get("prices_to_emit")
            if prices_to_emit is not None:
                steps.append(EmitStorePrices(prices_to_emit))

        elif task_type == "wishlist":
            updates = self._wishlist_service.apply_wishlist(self._cache, data)
            wishlist_to_emit = updates.get("wishlist_to_emit")
            if wishlist_to_emit is not None:
                steps.append(EmitWishlist(wishlist_to_emit))

        elif task_type == "achievements":
            updates = self._achievement_service.apply_achievements(self._cache, data)
            achievements_to_emit = updates.get("achievements_to_emit")
            if achievements_to_emit is not None:
                steps.append(EmitAchievements(achievements_to_emit))

        # 原逻辑：除了 "games" 类型外，均在此处持久化。
        if task_type != "games":
            steps.append(SaveStep("after_task"))

        return ProcessOutcome(steps=steps)

    def _finalize_games_steps(self) -> List[Step]:
        steps: List[Step] = []

        account_map = self._games_aggregator.finalize()

        primary_id = self._get_primary_id()
        updates = self._games_aggregation_service.apply_games_aggregation(self._cache, primary_id, account_map)

        summary_to_emit = updates.get("summary_to_emit")
        if summary_to_emit:
            steps.append(EmitPlayerSummary(summary_to_emit))

        games_to_emit = updates.get("games_to_emit")
        if games_to_emit is not None:
            steps.append(EmitGamesStats(games_to_emit))

        if updates.get("should_save"):
            steps.append(SaveStep("finalize"))

        return steps


__all__ = [
    "EmitPlayerSummary",
    "EmitGamesStats",
    "EmitStorePrices",
    "EmitWishlist",
    "EmitAchievements",
    "EmitError",
    "SaveStep",
    "Step",
    "ProcessOutcome",
    "SteamResultProcessor",
]
