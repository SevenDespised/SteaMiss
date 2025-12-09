try:
    from steam.webapi import WebAPI
except ImportError:
    WebAPI = None
    print("Warning: 'steam' library not found. Please install it via 'pip install steam'.")

import requests

class SteamClient:
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
                print(f"Failed to initialize WebAPI: {e}")
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
            # 库函数调用：直接传入参数，无需手动构建 URL
            response = self.api.ISteamUser.GetPlayerSummaries(steamids=steam_ids)
            # 库函数通常返回解析后的字典
            return response.get('response', {}).get('players', [])
        except Exception as e:
            print(f"Steam API Error (GetPlayerSummaries): {e}")
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
            # 库函数调用
            response = self.api.IPlayerService.GetOwnedGames(
                steamid=steam_id,
                include_appinfo=1,
                include_played_free_games=0,
                appids_filter=[],  # 显式传递空列表以满足某些库版本的验证要求
                include_free_sub=0,
                language='schinese',
                include_extended_appinfo=0
            )
            return response.get('response', {})
        except Exception as e:
            print(f"Steam API Error (GetOwnedGames): {e}")
            return None

    def get_steam_level(self, steam_id):
        """获取 Steam 等级"""
        self._ensure_api()
        if not self.api: return 0
        try:
            response = self.api.IPlayerService.GetSteamLevel(steamid=steam_id)
            return response.get('response', {}).get('player_level', 0)
        except Exception as e:
            print(f"Steam API Error (GetSteamLevel): {e}")
            return 0

    def get_app_details(self, app_ids):
        """
        获取游戏商店信息 (价格等)
        注意：这是非官方 API，有严格速率限制，且不能通过 steam 库直接调用
        """
        if not app_ids: return {}
        
        # 转换为逗号分隔字符串
        app_ids_str = ",".join(map(str, app_ids))
        url = "https://store.steampowered.com/api/appdetails"
        params = {
            "appids": app_ids_str,
            "filters": "price_overview",
            "cc": "cn", # 中国区价格
            "l": "schinese"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Steam Store API Error: {e}")
            return {}
            
    def get_wishlist(self, steam_id):
        """
        获取愿望单数据 (包含价格和折扣信息)
        URL: https://store.steampowered.com/wishlist/profiles/{steam_id}/wishlistdata/
        """
        url = f"https://store.steampowered.com/wishlist/profiles/{steam_id}/wishlistdata/"
        params = {
            "p": 0, 
            "cc": "cn",
            "l": "schinese"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Steam Wishlist Error: {e}")
            return None

    def get_player_inventory(self, steam_id, appid, contextid):
        """
        获取玩家库存
        注意：'steam' 库主要封装官方 WebAPI，而官方 WebAPI 的库存接口 (IEconService) 
        通常需要游戏开发者的 Publisher Key，普通 API Key 无法调用。
        因此，这里仍然需要使用 Steam 社区的公开 JSON 接口。
        """
        url = f"https://steamcommunity.com/inventory/{steam_id}/{app_id}/{context_id}"
        params = {'l': 'schinese', 'count': 5000}
        
        try:
            # 这里保留 requests，因为这是访问社区数据的标准方式
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Steam Inventory Request Error: {e}")
            return None
