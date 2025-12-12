from PyQt6.QtCore import QThread, pyqtSignal
import time
from src.api.steam_client import SteamClient

class SteamWorker(QThread):
    """后台工作线程，用于执行耗时的网络请求"""

    data_ready = pyqtSignal(dict)  # 信号：携带数据字典

    def __init__(self, api_key, steam_id, task_type="summary", extra_data=None):
        super().__init__()
        self.client = SteamClient(api_key)
        self.steam_id = steam_id
        self.task_type = task_type
        self.extra_data = extra_data  # 用于传递额外参数，如 appids

    def run(self):
        result = {"type": self.task_type, "data": None, "error": None, "steam_id": self.steam_id}

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
                        time.sleep(0.5)  # 礼貌性延迟，防止被封 IP
                    result["data"] = all_prices

            elif self.task_type == "inventory":
                inv_data = self.client.get_player_inventory(self.steam_id, 730, 2)
                if inv_data and "assets" in inv_data:
                    result["data"] = {"total_items": len(inv_data["assets"])}

            elif self.task_type == "wishlist":
                wishlist_data = self.client.get_wishlist(self.steam_id)

                discounted_games = []
                for appid, details in wishlist_data.items():
                    subs = details.get("subs", [])
                    if not subs:
                        continue

                    best_sub = None
                    max_discount = -1

                    for sub in subs:
                        discount = sub.get("discount_pct", 0) or 0
                        if discount > max_discount:
                            max_discount = discount
                            best_sub = sub

                    if best_sub and max_discount > 0:
                        price_str = best_sub.get("price", "")
                        image_url = details.get("capsule", "")
                        discounted_games.append(
                            {
                                "appid": appid,
                                "name": details.get("name", "Unknown"),
                                "discount_pct": max_discount,
                                "price": price_str,
                                "image": image_url,
                            }
                        )

                discounted_games.sort(key=lambda x: x["discount_pct"], reverse=True)
                result["data"] = discounted_games[:10]

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

                result["data"] = {
                    "summary": summary_data,
                    "games": games_payload,
                }

            elif self.task_type == "achievements":
                appids = self.extra_data
                if appids:
                    achievements_data = {}
                    for appid in appids:
                        stats = self.client.get_player_achievements(self.steam_id, appid)
                        if stats and "achievements" in stats:
                            ach_list = stats["achievements"]
                            total = len(ach_list)
                            unlocked = sum(1 for a in ach_list if a.get("achieved") == 1)
                            achievements_data[str(appid)] = {
                                "total": total,
                                "unlocked": unlocked
                            }
                        else:
                            # 标记为无成就或获取失败
                            achievements_data[str(appid)] = {"total": 0, "unlocked": 0}
                        
                        # 简单的限流
                        time.sleep(0.1)
                    result["data"] = achievements_data

        except Exception as e:
            result["error"] = str(e)
            print(f"Worker Error: {e}")

        self.data_ready.emit(result)


def build_games_payload(games, game_count):
    games_by_playtime = sorted(games, key=lambda x: x.get("playtime_forever", 0), reverse=True)
    games_by_recent = sorted(games, key=lambda x: x.get("rtime_last_played", 0), reverse=True)
    games_by_2weeks = sorted(games, key=lambda x: x.get("playtime_2weeks", 0), reverse=True)
    top_2weeks = [g for g in games_by_2weeks if g.get("playtime_2weeks", 0) > 0][:5]

    return {
        "count": game_count,
        "all_games": games,
        "top_games": games_by_playtime[:5],
        "recent_game": games_by_recent[0] if games_by_recent else None,
        "top_2weeks": top_2weeks,
        "total_playtime": sum(g.get("playtime_forever", 0) for g in games),
    }
