import logging

import requests

logger = logging.getLogger(__name__)

try:
    from steam.webapi import WebAPI
except ImportError:
    WebAPI = None
    logger.warning("'steam' library not found. Install via 'pip install steam'.")


class SteamClient:
    """
    Steam 网络客户端（HTTP/WebAPI 适配）。
    - 不依赖 Qt
    - 提供 Steam WebAPI 与部分 Store/Community 非官方接口的封装
    """

    def __init__(self, api_key):
        self.api_key = api_key
        self.api = None
        # 移除 __init__ 中的 WebAPI 初始化，改为懒加载
        # 因为 WebAPI(key=...) 会立即发起网络请求获取接口列表，这会阻塞主线程

    def _ensure_api(self):
        """确保 WebAPI 已初始化"""
        if self.api is None and WebAPI and self.api_key:
            try:
                self.api = WebAPI(key=self.api_key)
            except Exception as e:
                logger.exception("Failed to initialize WebAPI")
                # 这里不抛出异常，让后续调用自行处理 None

    def get_player_summaries(self, steam_ids):
        """
        获取玩家基本信息 (头像, 昵称, 状态)
        使用 steam.webapi.WebAPI 调用 ISteamUser.GetPlayerSummaries
        """
        self._ensure_api()
        if not self.api:
            return []

        try:
            response = self.api.ISteamUser.GetPlayerSummaries(steamids=steam_ids)
            return response.get("response", {}).get("players", [])
        except Exception as e:
            logger.exception("Steam API Error (GetPlayerSummaries): steam_ids=%s", steam_ids)
            return []

    def get_owned_games(self, steam_id):
        """
        获取拥有的游戏列表 (包含时长)
        使用 steam.webapi.WebAPI 调用 IPlayerService.GetOwnedGames
        """
        self._ensure_api()
        if not self.api:
            return None

        try:
            response = self.api.IPlayerService.GetOwnedGames(
                steamid=steam_id,
                include_appinfo=1,
                include_played_free_games=0,
                appids_filter=[],
                include_free_sub=0,
                language="schinese",
                include_extended_appinfo=0,
            )
            return response.get("response", {})
        except Exception as e:
            logger.exception("Steam API Error (GetOwnedGames): steam_id=%s", steam_id)
            return None

    def get_steam_level(self, steam_id):
        """获取 Steam 等级"""
        self._ensure_api()
        if not self.api:
            return 0
        try:
            response = self.api.IPlayerService.GetSteamLevel(steamid=steam_id)
            return response.get("response", {}).get("player_level", 0)
        except Exception as e:
            logger.exception("Steam API Error (GetSteamLevel): steam_id=%s", steam_id)
            return 0

    def get_app_price(self, app_ids):
        """
        获取游戏商店信息 (价格等)
        注意：这是非官方 API，有严格速率限制。
        """
        if not app_ids:
            return {}

        app_ids_str = ",".join(map(str, app_ids))
        url = "https://store.steampowered.com/api/appdetails"
        params = {"appids": app_ids_str, "filters": "price_overview", "cc": "cn", "l": "schinese"}

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.exception("Steam Store API Error: app_ids=%s", app_ids)
            return {}

    def get_player_achievements(self, steam_id, app_id):
        """
        获取玩家在特定游戏的成就统计
        调用 ISteamUserStats.GetPlayerAchievements
        """
        self._ensure_api()
        if not self.api:
            return None

        try:
            response = self.api.ISteamUserStats.GetPlayerAchievements(steamid=steam_id, appid=app_id, l="schinese")
            return response.get("playerstats", {})
        except Exception:
            logger.exception("Steam API Error (GetPlayerAchievements): steam_id=%s app_id=%s", steam_id, app_id)
            return None

    # --- 以下为原逻辑：保留不动（后续再考虑继续拆分/下沉） ---

    def get_all_apps(
        self,
        include_games=True,
        include_dlc=False,
        include_software=False,
        include_videos=False,
        include_hardware=False,
        if_modified_since=None,
        max_results=50000,
    ):
        self._ensure_api()

        all_apps = []
        last_appid = 0
        import time

        try:
            while True:
                try:
                    response = self.api.IStoreService.GetAppList(
                        include_games=include_games,
                        include_dlc=include_dlc,
                        include_software=include_software,
                        include_videos=include_videos,
                        include_hardware=include_hardware,
                        max_results=max_results,
                        language="schinese",
                    )
                    if last_appid > 0:
                        response = self.api.IStoreService.GetAppList(
                            include_games=include_games,
                            include_dlc=include_dlc,
                            include_software=include_software,
                            include_videos=include_videos,
                            include_hardware=include_hardware,
                            max_results=max_results,
                            language="schinese",
                            last_appid=last_appid,
                        )
                    if if_modified_since:
                        response = self.api.IStoreService.GetAppList(
                            include_games=include_games,
                            include_dlc=include_dlc,
                            include_software=include_software,
                            include_videos=include_videos,
                            include_hardware=include_hardware,
                            max_results=max_results,
                            language="schinese",
                            if_modified_since=if_modified_since,
                        )

                    data = response.get("response", {})
                    apps = data.get("apps", [])
                except TypeError:
                    url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
                    params = {
                        "key": self.api_key,
                        "include_games": str(include_games).lower(),
                        "include_dlc": str(include_dlc).lower(),
                        "include_software": str(include_software).lower(),
                        "include_videos": str(include_videos).lower(),
                        "include_hardware": str(include_hardware).lower(),
                        "max_results": max_results,
                        "language": "schinese",
                    }

                    if last_appid > 0:
                        params["last_appid"] = last_appid

                    if if_modified_since:
                        params["if_modified_since"] = if_modified_since

                    resp = requests.get(url, params=params, timeout=30)
                    if resp.status_code != 200:
                        logger.error("Steam API Error (GetAppList): HTTP %s", resp.status_code)
                        break

                    data = resp.json().get("response", {})
                    apps = data.get("apps", [])

                if not apps:
                    break

                all_apps.extend(apps)
                last_appid = apps[-1]["appid"]
                have_more_results = data.get("have_more_results", False)
                if not have_more_results:
                    break
                time.sleep(0.5)

        except Exception as e:
            logger.exception("Steam API Error (GetAppList)")

        return all_apps

    def get_apps_info(self, app_ids):
        """
        获取游戏基本信息 (名称, 图标等)
        由于 appdetails 接口多 ID 查询不稳定，改为逐个查询。
        """
        if not app_ids:
            return {}

        result = {}
        import time

        url = "https://store.steampowered.com/api/appdetails"
        
        for appid in app_ids:
            # 逐个查询，使用 filters=basic 减少数据量
            params = {"appids": appid, "filters": "basic", "cc": "cn", "l": "schinese"}
            try:
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # data 结构: {"730": {"success": true, "data": {...}}}
                    appid_str = str(appid)
                    if appid_str in data and data[appid_str].get("success"):
                        result[appid_str] = data[appid_str].get("data", {})
                
                # 避免请求过快
                time.sleep(0.1)
            except Exception as e:
                logger.exception("Steam API Error (get_apps_info): appid=%s", appid)
        
        return result

    def get_wishlist_app(self, steam_id):
        self._ensure_api()
        app_ids = []

        if self.api:
            try:
                response = self.api.IWishlistService.GetWishlist(steamid=steam_id)
                items = response.get("response", {}).get("items", [])
                app_ids = [item["appid"] for item in items]
            except Exception as e:
                logger.exception("Steam API Error (GetWishlistApp): steam_id=%s", steam_id)
        return app_ids

    def get_game_followed(self, steam_id):
        self._ensure_api()
        app_ids = []

        if self.api:
            try:
                response = self.api.IStoreService.GetGamesFollowed(steamid=steam_id)
                app_ids = response.get("response", {}).get("appids", [])
            except Exception as e:
                logger.exception("Steam API Error (GetGamesFollowedApp): steam_id=%s", steam_id)
        return app_ids

    def get_wishlist(self, steam_id):
        self._ensure_api()

        app_ids1 = self.get_wishlist_app(steam_id)
        app_ids2 = self.get_game_followed(steam_id)
        app_ids = list(set(app_ids1 + app_ids2))

        if app_ids:
            wishlist_dict = {}
            import time

            app_info_map = self.get_apps_info(app_ids)

            chunk_size = 50
            for i in range(0, len(app_ids), chunk_size):
                chunk = app_ids[i : i + chunk_size]
                details_map = self.get_app_price(chunk)

                for appid_str, data_wrapper in details_map.items():
                    if not data_wrapper.get("success"):
                        continue
                    data = data_wrapper.get("data", {})
                    if not isinstance(data, dict):
                        continue

                    price_overview = data.get("price_overview", {})
                    sub = {"discount_pct": price_overview.get("discount_percent", 0), "price": price_overview.get("final_formatted", "")}

                    info = app_info_map.get(str(appid_str), {})
                    name = info.get("name", "Unknown")

                    wishlist_dict[str(appid_str)] = {"subs": [sub], "name": name}

                if i + chunk_size < len(app_ids):
                    time.sleep(0.2)

            return wishlist_dict

        if str(steam_id).isdigit():
            url = f"https://store.steampowered.com/wishlist/profiles/{steam_id}/wishlistdata/"
        else:
            url = f"https://store.steampowered.com/wishlist/id/{steam_id}/wishlistdata/"

        params = {"p": 0, "cc": "cn", "l": "schinese"}
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.exception("Steam Wishlist Fallback Error: steam_id=%s", steam_id)

        return {}

    def get_player_inventory(self, steam_id, appid, contextid):
        url = f"https://steamcommunity.com/inventory/{steam_id}/{appid}/{contextid}"
        params = {"l": "schinese", "count": 5000}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception(
                "Steam Inventory Request Error: steam_id=%s appid=%s contextid=%s",
                steam_id,
                appid,
                contextid,
            )
            return None


__all__ = ["SteamClient"]


