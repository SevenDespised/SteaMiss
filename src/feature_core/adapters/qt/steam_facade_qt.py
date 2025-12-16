from PyQt6.QtCore import QObject, pyqtSignal

from typing import Optional

from src.feature_core.services.steam.games_aggregator import GamesAggregator
import os

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

from src.feature_core.services.steam.launcher_service import SteamLauncherService
from src.feature_core.adapters.qt.steam_task_service_qt import SteamTaskServiceQt
from src.feature_core.services.steam.account_service import SteamAccountService
from src.feature_core.domain.steam_account_models import SteamAccountPolicy
from src.feature_core.services.steam.query_service import SteamQueryService
from src.feature_core.services.steam.dataset_service import SteamDatasetService
from src.feature_core.services.steam.games_aggregation_service import SteamGamesAggregationService
from src.feature_core.services.steam.profile_service import SteamProfileService
from src.feature_core.services.steam.price_service import SteamPriceService
from src.feature_core.services.steam.wishlist_service import SteamWishlistService
from src.feature_core.services.steam.achievement_service import SteamAchievementService
from src.storage.steam_repository import SteamRepository


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

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.cache = {}
        self._policy_cache: Optional[SteamAccountPolicy] = None

        self.games_aggregator = GamesAggregator()
        self.launcher_service = SteamLauncherService()
        self.repository = SteamRepository()
        self.service = SteamTaskServiceQt()  # Qt worker：异步抓取
        # 纯业务子域（不依赖 Qt）：现阶段不做“多 service 协同”，Qt 直接调用这些子域
        self.account_service = SteamAccountService()
        self.query_service = SteamQueryService()
        self.dataset_service = SteamDatasetService()
        self.games_aggregation_service = SteamGamesAggregationService()
        self.profile_service = SteamProfileService()
        self.price_service = SteamPriceService()
        self.wishlist_service = SteamWishlistService()
        self.achievement_service = SteamAchievementService()

        self.repository.error_occurred.connect(self.on_error.emit)
        self.service.task_finished.connect(self._handle_worker_result)

        self.cache = self.repository.load_data()

        self.fetch_games_stats()
        self.fetch_player_summary()

    def invalidate_account_policy_cache(self) -> None:
        """
        使账号策略缓存失效。
        当你在运行时修改了 config（steam_api_key/steam_id/steam_alt_ids）后，可手动调用一次。
        """
        self._policy_cache = None

    def on_credentials_changed(self) -> None:
        """
        账号凭证发生变化后的最小刷新动作：
        - 失效账号策略缓存
        - 重新抓取 games_stats + player_summary

        说明：
        - 不清理旧 cache（历史数据保留符合你的预期）
        - 不自动抓取 wishlist/achievements/prices（这些较慢，继续由用户手动触发）
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

    def _get_all_account_ids(self):
        return list(self._policy().account_ids)

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
        if result.get("error"):
            if result.get("type") == "games" and self.games_aggregator:
                done = self.games_aggregator.mark_error()
                if done:
                    self._finalize_games_results()
            self.on_error.emit(result["error"])
            return

        task_type = result.get("type")
        data = result.get("data")
        if data is None:
            return

        if task_type == "summary":
            updates = self.profile_service.apply_summary(self.cache, data)
            summary_to_emit = updates.get("summary_to_emit")
            if summary_to_emit:
                self.on_player_summary.emit(summary_to_emit)
        elif task_type in ("games", "profile_and_games"):
            steam_id = result.get("steam_id")
            if task_type == "profile_and_games":
                games_data = data.get("games") if data else None
                summary_data = data.get("summary") if data else None
            else:
                games_data = data
                summary_data = None

            if self.games_aggregator:
                if games_data is None:
                    done = self.games_aggregator.mark_error()
                    if done:
                        self._finalize_games_results()
                else:
                    done = self.games_aggregator.add_result(steam_id, games_data, summary_data)
                    if done:
                        self._finalize_games_results()

        elif task_type == "store_prices":
            updates = self.price_service.apply_store_prices(self.cache, data)
            prices_to_emit = updates.get("prices_to_emit")
            if prices_to_emit is not None:
                self.on_store_prices.emit(prices_to_emit)
        elif task_type == "wishlist":
            updates = self.wishlist_service.apply_wishlist(self.cache, data)
            wishlist_to_emit = updates.get("wishlist_to_emit")
            if wishlist_to_emit is not None:
                self.on_wishlist_data.emit(wishlist_to_emit)
        elif task_type == "achievements":
            updates = self.achievement_service.apply_achievements(self.cache, data)
            achievements_to_emit = updates.get("achievements_to_emit")
            if achievements_to_emit is not None:
                self.on_achievements_data.emit(achievements_to_emit)

        if task_type != "games":
            self.repository.save_data(self.cache)

    def _finalize_games_results(self):
        primary_data, aggregated, account_map = self.games_aggregator.finalize()

        primary_id = self._policy().primary_id
        updates = self.games_aggregation_service.apply_games_aggregation(self.cache, primary_id, primary_data, aggregated, account_map)

        summary_to_emit = updates.get("summary_to_emit")
        if summary_to_emit:
            self.on_player_summary.emit(summary_to_emit)

        games_to_emit = updates.get("games_to_emit")
        if games_to_emit is not None:
            self.on_games_stats.emit(games_to_emit)

        if updates.get("should_save"):
            self.repository.save_data(self.cache)

    def get_game_datasets(self):
        policy = self._policy()
        return self.dataset_service.build_game_datasets(self.cache, policy.primary_id, policy.alt_ids)

    def _ensure_aggregated_cache(self):
        self.dataset_service.ensure_aggregated_cache(self.cache)

    def _get_primary_games_cache(self):
        primary_id = self._policy().primary_id
        return self.query_service.get_primary_games_cache(self.cache, primary_id)

    def launch_game(self, appid):
        plan = self.launcher_service.build_launch_game(appid)
        if not plan:
            return
        try:
            os.startfile(plan.primary_uri)
        except Exception as e:
            self.on_error.emit(f"Failed to launch game {appid}: {e}")

    def open_page(self, page_type):
        plan = self.launcher_service.build_open_page(page_type)
        if not plan:
            return
        try:
            os.startfile(plan.primary_uri)
        except Exception as e:
            if plan.fallback_url:
                try:
                    QDesktopServices.openUrl(QUrl(plan.fallback_url))
                    return
                except Exception:
                    pass
            self.on_error.emit(f"Failed to open steam page {page_type}: {e}")


__all__ = ["SteamFacadeQt"]


