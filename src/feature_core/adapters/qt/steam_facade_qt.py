import logging
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from src.feature_core.services.steam.games_aggregator import GamesAggregator
from src.feature_core.services.steam.account_service import SteamAccountService
from src.feature_core.domain.steam_account_models import SteamAccountPolicy
from src.feature_core.services.steam.query_service import SteamQueryService
from src.feature_core.services.steam.dataset_service import SteamDatasetService
from src.feature_core.services.steam.games_aggregation_service import SteamGamesAggregationService
from src.feature_core.services.steam.profile_service import SteamProfileService
from src.feature_core.services.steam.price_service import SteamPriceService
from src.feature_core.services.steam.wishlist_service import SteamWishlistService
from src.feature_core.services.steam.achievement_service import SteamAchievementService
from src.feature_core.services.steam.steam_result_processor import (
    EmitAchievements,
    EmitError,
    EmitGamesStats,
    EmitPlayerSummary,
    EmitStorePrices,
    EmitWishlist,
    SaveStep,
    SteamResultProcessor,
)
from src.feature_core.services.steam.steam_ports import SteamRepositoryPort, SteamTaskServicePort


logger = logging.getLogger(__name__)


class SteamFacadeQt(QObject):
    """
    Qt 对外入口：SteamFacadeQt
    - 负责协调 UI 与异步任务（通过 Qt signals）
    - 内部维护缓存与聚合结果
    """

    on_player_summary = pyqtSignal(dict)
    on_games_stats = pyqtSignal(dict)
    on_store_prices = pyqtSignal(dict)
    on_wishlist_data = pyqtSignal(list)
    on_achievements_data = pyqtSignal(dict)
    on_error = pyqtSignal(str)

    def __init__(
        self,
        config_manager,
        *,
        repository: SteamRepositoryPort,
        task_service: SteamTaskServicePort,
    ):
        super().__init__()
        self.config = config_manager
        self.cache = {}
        self._policy_cache: Optional[SteamAccountPolicy] = None

        self._result_processor: Optional[SteamResultProcessor] = None

        self.games_aggregator = GamesAggregator()
        self.repository = repository
        self.service = task_service  # Qt worker：异步抓取
        # 纯业务子域（不依赖 Qt）：现阶段不做“多 service 协同”，Qt 直接调用这些子域
        self.account_service = SteamAccountService()
        self.query_service = SteamQueryService()
        self.dataset_service = SteamDatasetService()
        self.games_aggregation_service = SteamGamesAggregationService()
        self.profile_service = SteamProfileService()
        self.price_service = SteamPriceService()
        self.wishlist_service = SteamWishlistService()
        self.achievement_service = SteamAchievementService()

        try:
            self.repository.set_error_handler(self.on_error.emit)
        except Exception:
            logger.exception("Failed to set SteamRepository error handler")
        self.service.task_finished.connect(self._handle_worker_result)

        self.cache = self.repository.load_data()

        # 启动/离线：若 games 缺失，则基于本地 games_accounts 聚合一次并落盘
        if self.games_aggregation_service.ensure_games_from_accounts(self.cache):
            self.repository.save_data(self.cache)

        self._result_processor = SteamResultProcessor(
            cache=self.cache,
            games_aggregator=self.games_aggregator,
            get_primary_id=lambda: self._policy().primary_id,
            games_aggregation_service=self.games_aggregation_service,
            profile_service=self.profile_service,
            price_service=self.price_service,
            wishlist_service=self.wishlist_service,
            achievement_service=self.achievement_service,
        )

        self.fetch_player_summary()
        self.fetch_games_stats() 

    def invalidate_account_policy_cache(self) -> None:
        """
        使账号策略缓存失效。
        """
        self._policy_cache = None

    def on_credentials_changed(self) -> None:
        """
        账号凭证发生变化后的最小刷新动作：
        - 失效账号策略缓存
        - 重新抓取 games_stats + player_summary
        """
        self.invalidate_account_policy_cache()
        self.fetch_games_stats()
        self.fetch_player_summary()

    def _policy(self) -> SteamAccountPolicy:
        """
        统一入口：获取账号策略（带缓存）。
        """
        if self._policy_cache is None:
            self._policy_cache = self.account_service.build_policy(self.config)
        return self._policy_cache

    def _get_primary_credentials(self):
        policy = self._policy()
        return policy.api_key, policy.primary_id

    def fetch_player_summary(self):
        key, sid = self._get_primary_credentials()
        if not key or not sid:
            return
        self.service.start_task(key, sid, "summary")

    def fetch_games_stats(self):
        policy = self._policy()
        key = policy.api_key
        ids = policy.account_ids
        if not key or not ids:
            return

        primary_id = policy.primary_id or ids[0]
        self.games_aggregator.begin(ids, primary_id)

        for sid in ids:
            self.service.start_task(key, sid, "profile_and_games", steam_id=sid)

    def fetch_store_prices(self, appids):
        key, sid = self._get_primary_credentials()
        if not key or not sid:
            return
        self.service.start_task(key, sid, "store_prices", extra_data=appids)

    def fetch_wishlist(self):
        key, sid = self._get_primary_credentials()
        if not key or not sid:
            return
        self.service.start_task(key, sid, "wishlist")

    def fetch_achievements(self, appids):
        key, sid = self._get_primary_credentials()
        if not key or not sid:
            return
        self.service.start_task(key, sid, "achievements", extra_data=appids)

    def get_recent_games(self, limit=3):
        primary_id = self._policy().primary_id
        return self.query_service.get_recent_games(self.cache, primary_id, limit=limit)

    def search_games(self, keyword):
        primary_id = self._policy().primary_id
        return self.query_service.search_games(self.cache, primary_id, keyword)

    def _handle_worker_result(self, result):
        if not self._result_processor:
            return

        task_type = (result or {}).get("type")
        steam_id = (result or {}).get("steam_id")
        error = (result or {}).get("error")
        tb = (result or {}).get("traceback")
        if error:
            if tb:
                logger.error(
                    "Steam worker error: type=%s steam_id=%s error=%s\n%s",
                    task_type,
                    steam_id,
                    error,
                    tb,
                )
            else:
                logger.error(
                    "Steam worker error: type=%s steam_id=%s error=%s",
                    task_type,
                    steam_id,
                    error,
                )

        try:
            outcome = self._result_processor.process(result)
        except Exception:
            logger.exception(
                "SteamResultProcessor.process failed: type=%s steam_id=%s",
                task_type,
                steam_id,
            )
            try:
                self.on_error.emit(f"Steam processor failed: {task_type}")
            except Exception:
                logger.exception("SteamFacadeQt failed to emit on_error")
            return

        emitters = {
            EmitPlayerSummary: self.on_player_summary.emit,
            EmitGamesStats: self.on_games_stats.emit,
            EmitStorePrices: self.on_store_prices.emit,
            EmitWishlist: self.on_wishlist_data.emit,
            EmitAchievements: self.on_achievements_data.emit,
            EmitError: self.on_error.emit,
        }

        for step in outcome.steps:
            if isinstance(step, SaveStep):
                try:
                    self.repository.save_data(self.cache)
                except Exception:
                    logger.exception("Failed to save steam cache: type=%s steam_id=%s", task_type, steam_id)
                continue

            emitter = emitters.get(type(step))
            if emitter is not None:
                try:
                    emitter(step.payload)
                except Exception:
                    logger.exception(
                        "SteamFacadeQt emitter failed: type=%s step=%s",
                        task_type,
                        type(step).__name__,
                    )

    def get_game_datasets(self):
        policy = self._policy()
        return self.dataset_service.build_game_datasets(self.cache, policy.primary_id, policy.alt_ids)

__all__ = ["SteamFacadeQt"]


