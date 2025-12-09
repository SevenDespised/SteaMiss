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

    def get_app_price(self, app_ids):
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
            
    def get_apps_info(self, app_ids):
        """
        批量获取游戏基本信息 (如名称)
        使用 IStoreService.GetAppList
        """
        if not app_ids or not self.api_key:
            return {}

        app_info_map = {}
        import time
        try:
            # 分批获取信息，每次 30 个
            for i in range(0, len(app_ids), 30):
                chunk = app_ids[i:i+30]
                # IStoreService.GetAppList 需要特殊参数构造
                # 这里使用 requests 手动构造，因为 steam 库可能不支持复杂的数组参数
                url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
                params = {
                    "key": self.api_key,
                    "include_games": "true",
                    "language": "schinese"
                }
                # 手动添加 appids 参数
                for idx, appid in enumerate(chunk):
                    params[f"appids[{idx}]"] = appid
                    
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    apps = resp.json().get('response', {}).get('apps', [])
                    for app in apps:
                        app_info_map[str(app['appid'])] = app
                time.sleep(0.2)
        except Exception as e:
            print(f"Steam API Error (IStoreService): {e}")
            
        return app_info_map

    def get_wishlist(self, steam_id):
        """
        获取愿望单数据，并转换为 SteamWorker 期望的格式
        优先使用 IWishlistService 获取列表 + Store API 获取价格
        """
        self._ensure_api()
        
        app_ids = []
        # 1. 尝试获取 AppID 列表 (IWishlistService)
        if self.api:
            try:
                response = self.api.IWishlistService.GetWishlist(steamid=steam_id)
                items = response.get('response', {}).get('items', [])
                app_ids = [item['appid'] for item in items]
            except Exception as e:
                print(f"Steam API Error (GetWishlist): {e}")

        # Fallback: 如果 steam 库失败，尝试直接请求 API
        if not app_ids and self.api_key:
             try:
                url = "https://api.steampowered.com/IWishlistService/GetWishlist/v1/"
                params = {"key": self.api_key, "steamid": steam_id}
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    items = response.json().get('response', {}).get('items', [])
                    app_ids = [item['appid'] for item in items]
             except Exception as e:
                 print(f"Steam API Fallback Error (GetWishlist): {e}")

        # 2. 如果拿到了 AppID，去商店查价格并转换格式
        if app_ids:
            wishlist_dict = {}
            import time
            
            # 2.1 获取基本信息 (Name) - 使用 IStoreService (WebAPI)
            app_info_map = self.get_apps_info(app_ids)

            # 2.2 获取价格 (Store API)
            # 分批查询，每次 20 个
            chunk_size = 20
            for i in range(0, len(app_ids), chunk_size):
                chunk = app_ids[i:i+chunk_size]
                details_map = self.get_app_price(chunk)
                
                for appid_str, data_wrapper in details_map.items():
                    if not data_wrapper.get('success'): continue
                    data = data_wrapper.get('data', {})
                    
                    # 确保 data 是字典，防止 API 返回空列表导致报错
                    if not isinstance(data, dict):
                        continue

                    # 转换结构以匹配 SteamWorker
                    price_overview = data.get('price_overview', {})
                    
                    # 构造兼容的 sub 结构
                    sub = {
                        'discount_pct': price_overview.get('discount_percent', 0),
                        'price': price_overview.get('final_formatted', ''),
                    }
                    
                    # 从 app_info_map 获取名称
                    info = app_info_map.get(str(appid_str), {})
                    name = info.get('name', 'Unknown')
                    
                    wishlist_dict[str(appid_str)] = {
                        'subs': [sub],
                        'name': name
                    }
                # 简单限流
                if i + chunk_size < len(app_ids):
                    time.sleep(0.2)
            
            return wishlist_dict

        # 3. 如果上面都失败了，尝试直接访问 wishlistdata (最后的手段)
        # 判断 steam_id 类型：纯数字认为是 64位 ID，否则认为是自定义 ID
        if str(steam_id).isdigit():
            url = f"https://store.steampowered.com/wishlist/profiles/{steam_id}/wishlistdata/"
        else:
            url = f"https://store.steampowered.com/wishlist/id/{steam_id}/wishlistdata/"

        params = {"p": 0, "cc": "cn", "l": "schinese"}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Steam Wishlist Fallback Error: {e}")
            
        return {}

    def get_player_inventory(self, steam_id, appid, contextid):
        """
        获取玩家库存
        注意：'steam' 库主要封装官方 WebAPI，而官方 WebAPI 的库存接口 (IEconService) 
        通常需要游戏开发者的 Publisher Key，普通 API Key 无法调用。
        因此，这里仍然需要使用 Steam 社区的公开 JSON 接口。
        """
        # 修正变量名 app_id -> appid, context_id -> contextid
        url = f"https://steamcommunity.com/inventory/{steam_id}/{appid}/{contextid}"
        params = {'l': 'schinese', 'count': 5000}
        
        try:
            # 这里保留 requests，因为这是访问社区数据的标准方式
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Steam Inventory Request Error: {e}")
            return None
