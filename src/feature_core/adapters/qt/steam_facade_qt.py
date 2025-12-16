from PyQt6.QtCore import QObject, pyqtSignal

from src.feature_core.steam_support.steam_aggregator import GamesAggregator, merge_games
from src.feature_core.steam_support.steam_launcher import SteamLauncher
from src.feature_core.steam_support.steam_service import SteamService
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

        self.games_aggregator = GamesAggregator()
        self.launcher = SteamLauncher()
        self.repository = SteamRepository()
        self.service = SteamService()

        self.launcher.error_occurred.connect(self.on_error.emit)
        self.repository.error_occurred.connect(self.on_error.emit)
        self.service.task_finished.connect(self._handle_worker_result)

        self.cache = self.repository.load_data()

        key, sid = self._get_primary_credentials()
        if key and sid:
            self.fetch_games_stats()
            self.fetch_player_summary()

    def _get_primary_credentials(self):
        key = self.config.get("steam_api_key")
        sid = self.config.get("steam_id")
        return key, sid

    def _get_all_account_ids(self):
        ids = []
        primary = self.config.get("steam_id")
        if not primary:
            return ids

        ids.append(primary)
        alt_ids = self.config.get("steam_alt_ids", [])
        if isinstance(alt_ids, list):
            for sid in alt_ids:
                if sid and sid not in ids:
                    ids.append(sid)
        return ids

    def fetch_player_summary(self):
        key, sid = self._get_primary_credentials()
        if not key or not sid:
            return
        self.service.start_task(key, sid, "summary")

    def fetch_games_stats(self):
        key = self.config.get("steam_api_key")
        ids = self._get_all_account_ids()
        if not key or not ids:
            return

        primary_id = ids[0]
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
        games_cache = self._get_primary_games_cache()
        if not games_cache or not games_cache.get("all_games"):
            return []
        all_games = games_cache["all_games"]
        return sorted(all_games, key=lambda x: x.get("rtime_last_played", 0), reverse=True)[:limit]

    def search_games(self, keyword):
        games_cache = self._get_primary_games_cache()
        if not games_cache or not games_cache.get("all_games"):
            return []
        keyword = (keyword or "").lower()
        if not keyword:
            return []
        results = []
        for game in games_cache["all_games"]:
            name = (game.get("name", "") or "").lower()
            if keyword in name:
                results.append(game)
        return results

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
            self.cache["summary"] = data
            self.on_player_summary.emit(data)
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
            if "prices" not in self.cache:
                self.cache["prices"] = {}
            self.cache["prices"].update(data)
            self.on_store_prices.emit(data)
        elif task_type == "wishlist":
            self.cache["wishlist"] = data
            self.on_wishlist_data.emit(data)
        elif task_type == "achievements":
            if "achievements" not in self.cache:
                self.cache["achievements"] = {}
            self.cache["achievements"].update(data)
            self.on_achievements_data.emit(data)

        if task_type != "games":
            self.repository.save_data(self.cache)

    def _finalize_games_results(self):
        primary_data, aggregated, account_map = self.games_aggregator.finalize()

        if account_map:
            self.cache["games_accounts"] = account_map

        primary_id = self.config.get("steam_id")
        if primary_data:
            self.cache["games_primary"] = primary_data

        if primary_id and account_map and primary_id in account_map:
            primary_summary = account_map[primary_id].get("summary")
            if primary_summary:
                self.cache["summary"] = primary_summary
                self.on_player_summary.emit(primary_summary)

        if aggregated is not None:
            self.cache["games"] = aggregated
            self.on_games_stats.emit(aggregated)
            self.repository.save_data(self.cache)

    def get_game_datasets(self):
        datasets = []
        self._ensure_aggregated_cache()

        aggregated = self.cache.get("games")
        if aggregated is not None:
            datasets.append({"key": "total", "label": "总计", "steam_id": None, "data": aggregated, "summary": None})

        accounts = dict(self.cache.get("games_accounts", {}) or {})
        primary_id = self.config.get("steam_id")
        if primary_id and primary_id not in accounts and "games_primary" in self.cache:
            accounts[primary_id] = {"games": self.cache["games_primary"], "summary": self.cache.get("summary")}
        if primary_id and primary_id in accounts:
            primary_entry = accounts[primary_id]
            games_data = primary_entry.get("games")
            if games_data:
                datasets.append(
                    {
                        "key": "primary",
                        "label": "主账号",
                        "steam_id": primary_id,
                        "data": games_data,
                        "summary": primary_entry.get("summary") or self.cache.get("summary"),
                    }
                )

        alt_ids = self.config.get("steam_alt_ids", [])
        if isinstance(alt_ids, list):
            sub_index = 1
            for sid in alt_ids:
                entry = accounts.get(sid)
                if entry and entry.get("games"):
                    datasets.append(
                        {
                            "key": f"sub_{sub_index}",
                            "label": f"子账号{sub_index}",
                            "steam_id": sid,
                            "data": entry.get("games"),
                            "summary": entry.get("summary"),
                        }
                    )
                    sub_index += 1

        return datasets

    def _ensure_aggregated_cache(self):
        accounts = self.cache.get("games_accounts", {})
        if not accounts:
            if "games_primary" in self.cache:
                self.cache["games"] = self.cache["games_primary"]
            return

        results = []
        for sid, data in accounts.items():
            if data.get("games"):
                results.append({"steam_id": sid, "games": data["games"], "summary": data.get("summary")})

        if results:
            self.cache["games"] = merge_games(results)

    def _get_primary_games_cache(self):
        primary_id = self.config.get("steam_id")
        if not primary_id:
            return None
        if "games_primary" in self.cache:
            return self.cache["games_primary"]
        if "games" in self.cache:
            return self.cache["games"]
        return None

    def launch_game(self, appid):
        self.launcher.launch_game(appid)

    def open_page(self, page_type):
        self.launcher.open_page(page_type)


__all__ = ["SteamFacadeQt"]


