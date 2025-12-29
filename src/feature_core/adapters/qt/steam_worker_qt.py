from PyQt6.QtCore import QThread, pyqtSignal
import logging
import time
import traceback

from src.feature_core.adapters.http.steam_client import SteamClient
from src.feature_core.services.steam.achievement_stats_service import summarize_achievements
from src.feature_core.services.steam.games_payload_service import build_games_payload
from src.feature_core.services.steam.wishlist_discount_service import build_discounted_wishlist_items


logger = logging.getLogger(__name__)


class SteamWorker(QThread):
    """后台工作线程，用于执行耗时的网络请求（Qt）。"""

    data_ready = pyqtSignal(dict)

    def __init__(self, api_key, steam_id, task_type="summary", extra_data=None):
        super().__init__()
        self.client = SteamClient(api_key)
        self.steam_id = steam_id
        self.task_type = task_type
        self.extra_data = extra_data

    def run(self):
        result = {
            "type": self.task_type,
            "data": None,
            "error": None,
            "steam_id": self.steam_id,
            "traceback": None,
        }

        if not self.client.api_key or not self.steam_id:
            result["error"] = "Missing API Key or Steam ID"
            self.data_ready.emit(result)
            return

        try:
            if self.task_type == "summary":
                players = self.client.get_player_summaries(self.steam_id)
                level = self.client.get_steam_level(self.steam_id)

                if players:
                    data = players[0]
                    data["steam_level"] = level
                    result["data"] = data
                else:
                    result["error"] = "Failed to fetch player summary"

            elif self.task_type == "games":
                games_data = self.client.get_owned_games(self.steam_id)
                if games_data:
                    games = games_data.get("games", [])
                    result["data"] = build_games_payload(games, games_data.get("game_count", 0))
                else:
                    result["error"] = "Failed to fetch games data (API returned None)"

            elif self.task_type == "store_prices":
                appids = self.extra_data
                if appids:
                    chunk_size = 20
                    all_prices = {}
                    for i in range(0, len(appids), chunk_size):
                        chunk = appids[i : i + chunk_size]
                        prices = self.client.get_app_price(chunk)
                        if prices:
                            all_prices.update(prices)
                        time.sleep(0.5)
                    result["data"] = all_prices

            elif self.task_type == "inventory":
                inv_data = self.client.get_player_inventory(self.steam_id, 730, 2)
                if inv_data and "assets" in inv_data:
                    result["data"] = {"total_items": len(inv_data["assets"])}

            elif self.task_type == "wishlist":
                wishlist_data = self.client.get_wishlist(self.steam_id)
                result["data"] = build_discounted_wishlist_items(wishlist_data, limit=10)

            elif self.task_type == "profile_and_games":
                players = self.client.get_player_summaries(self.steam_id)
                level = self.client.get_steam_level(self.steam_id)
                summary_data = None
                if players:
                    summary_data = players[0]
                    summary_data["steam_level"] = level

                games_data = self.client.get_owned_games(self.steam_id)
                games_payload = None
                if games_data:
                    games = games_data.get("games", [])
                    games_payload = build_games_payload(games, games_data.get("game_count", 0))

                result["data"] = {"summary": summary_data, "games": games_payload}

            elif self.task_type == "achievements":
                appids = self.extra_data
                if appids:
                    achievements_data = {}
                    for appid in appids:
                        stats = self.client.get_player_achievements(self.steam_id, appid)
                        achievements_data[str(appid)] = summarize_achievements(stats)

                        time.sleep(0.1)
                    result["data"] = achievements_data

        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            logger.exception(
                "SteamWorker failed: task_type=%s steam_id=%s",
                self.task_type,
                self.steam_id,
            )

        self.data_ready.emit(result)
__all__ = ["SteamWorker"]


