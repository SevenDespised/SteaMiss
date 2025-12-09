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
        if WebAPI and self.api_key:
            # WebAPI 初始化
            self.api = WebAPI(key=self.api_key)

    def get_player_summaries(self, steam_ids):
        """
        获取玩家基本信息 (头像, 昵称, 状态)
        使用 steam.webapi.WebAPI 调用 ISteamUser.GetPlayerSummaries
        """
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
        if not self.api: 
            return None

        try:
            # 库函数调用
            response = self.api.IPlayerService.GetOwnedGames(
                steamid=steam_id,
                include_appinfo=1,
                include_played_free_games=0
            )
            return response.get('response', {})
        except Exception as e:
            print(f"Steam API Error (GetOwnedGames): {e}")
            return None

    def get_player_inventory(self, steam_id, app_id=730, context_id=2):
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
