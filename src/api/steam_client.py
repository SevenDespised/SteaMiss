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

    def get_player_achievements(self, steam_id, app_id):
        """
        获取玩家在特定游戏的成就统计
        调用 ISteamUserStats.GetPlayerAchievements
        """
        self._ensure_api()
        if not self.api: return None
        
        try:
            # 注意：GetPlayerAchievements 需要游戏有成就系统，否则可能报错或返回空
            response = self.api.ISteamUserStats.GetPlayerAchievements(
                steamid=steam_id,
                appid=app_id,
                l='schinese'
            )
            return response.get('playerstats', {})
        except Exception as e:
            # 很多游戏没有成就，或者 API 调用失败是正常的
            # print(f"Steam API Error (GetPlayerAchievements {app_id}): {e}")
            return None
            
    def get_all_apps(self, include_games=True, include_dlc=False, include_software=False, 
                     include_videos=False, include_hardware=False, if_modified_since=None, max_results=50000):
        """
        获取Steam商店所有可用应用列表
        使用 IStoreService.GetAppList 接口，支持分页获取全部数据
        
        参数:
            include_games: 是否包含游戏
            include_dlc: 是否包含DLC
            include_software: 是否包含软件
            include_videos: 是否包含视频
            include_hardware: 是否包含硬件
            if_modified_since: Unix时间戳，仅返回此时间后修改的应用
            max_results: 每次请求的最大结果数（默认50000，建议不超过50000）
            
        返回:
            包含所有app信息的列表，每个app包含 appid, name, last_modified, price_change_number 等字段
        """
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
                        language='schinese'
                    )
                    if last_appid > 0:
                        response = self.api.IStoreService.GetAppList(
                            include_games=include_games,
                            include_dlc=include_dlc,
                            include_software=include_software,
                            include_videos=include_videos,
                            include_hardware=include_hardware,
                            max_results=max_results,
                            language='schinese',
                            last_appid=last_appid
                        )
                    if if_modified_since:
                        response = self.api.IStoreService.GetAppList(
                            include_games=include_games,
                            include_dlc=include_dlc,
                            include_software=include_software,
                            include_videos=include_videos,
                            include_hardware=include_hardware,
                            max_results=max_results,
                            language='schinese',
                            if_modified_since=if_modified_since
                        )
                    
                    data = response.get('response', {})
                    apps = data.get('apps', [])
                except TypeError:
                    # WebAPI 不支持该参数组合，fallback 到 requests
                    url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
                    params = {
                        "key": self.api_key,
                        "include_games": str(include_games).lower(),
                        "include_dlc": str(include_dlc).lower(),
                        "include_software": str(include_software).lower(),
                        "include_videos": str(include_videos).lower(),
                        "include_hardware": str(include_hardware).lower(),
                        "max_results": max_results,
                        "language": "schinese"
                    }
                    
                    if last_appid > 0:
                        params["last_appid"] = last_appid
                        
                    if if_modified_since:
                        params["if_modified_since"] = if_modified_since
                    
                    resp = requests.get(url, params=params, timeout=30)
                    if resp.status_code != 200:
                        print(f"Steam API Error (GetAppList): HTTP {resp.status_code}")
                        break
                    
                    data = resp.json().get('response', {})
                    apps = data.get('apps', [])
                
                if not apps:
                    # 没有更多数据了
                    break
                    
                all_apps.extend(apps)
                
                # 获取最后一个appid，用于下次请求
                last_appid = apps[-1]['appid']
                
                # 检查是否还有更多数据
                have_more_results = data.get('have_more_results', False)
                if not have_more_results:
                    break
                    
                # 简单限流，避免触发速率限制
                time.sleep(0.5)
                
                print(f"已获取 {len(all_apps)} 个应用，继续获取...")
                
        except Exception as e:
            print(f"Steam API Error (GetAppList): {e}")
            
        return all_apps
    
    def get_apps_info(self, app_ids, max_results=50000):
        """
        批量获取游戏基本信息 (如名称) - 高效范围查询
        只获取包含目标appid的应用范围，避免下载整个Steam应用库
        
        策略：
        1. 找出目标appid中的最小值
        2. 从 min_appid - 1 开始，获取 max_results 个应用
        3. 从结果中筛选出目标appid
        4. 更新 min_appid 为还未找到的最小appid
        5. 重复直到找到全部或遍历完整个应用库
        
        参数:
            app_ids: 要查询的appid列表
            max_results: 每次请求的结果数量（默认50000）
        
        返回:
            app_info_map: 以appid为key的应用信息字典
        """
        self._ensure_api()
        if not app_ids or not self.api:
            return {}

        app_info_map = {}
        app_id_set = set(int(aid) for aid in app_ids)
        found_ids = set()
        import time
        
        try:
            # 按升序排序，找出最小和最大appid
            sorted_ids = sorted(app_id_set)
            min_appid = sorted_ids[0]
            max_appid = sorted_ids[-1]
            
            print(f"开始查询 {len(app_id_set)} 个应用，范围: {min_appid} - {max_appid}")
            
            # 从最小appid-1开始循环查询
            last_appid = min_appid - 1
            iteration = 0
            
            while len(found_ids) < len(app_id_set):
                iteration += 1
                try:
                    response = self.api.IStoreService.GetAppList(
                        include_games=True,
                        include_dlc=True,
                        include_software=False,
                        include_videos=False,
                        include_hardware=False,
                        max_results=max_results,
                        last_appid=last_appid if last_appid > 0 else None
                    )
                    data = response.get('response', {})
                    apps = data.get('apps', [])
                except TypeError:
                    # WebAPI 可能不支持该参数，fallback 到 requests
                    url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
                    params = {
                        "key": self.api_key,
                        "include_games": "true",
                        "include_dlc": "true",
                        "include_software": "false",
                        "include_videos": "false",
                        "include_hardware": "false",
                        "max_results": max_results,
                        "language": "schinese"
                    }
                    
                    if last_appid > 0:
                        params["last_appid"] = last_appid
                    
                    resp = requests.get(url, params=params, timeout=30)
                    if resp.status_code != 200:
                        print(f"Steam API Error (GetAppList): HTTP {resp.status_code}")
                        break
                    
                    data = resp.json().get('response', {})
                    apps = data.get('apps', [])
                
                if not apps:
                    # 没有更多数据了，商店已遍历完整
                    print(f"已遍历完整个Steam应用库，停止查询")
                    break
                
                # 在这批结果中筛选出目标appid
                batch_found = 0
                for app in apps:
                    appid = app['appid']
                    if appid in app_id_set and appid not in found_ids:
                        app_info_map[str(appid)] = app
                        found_ids.add(appid)
                        batch_found += 1
                
                last_appid = apps[-1]['appid']
                print(f"[迭代 {iteration}] 获取 {len(apps)} 个应用 (appid范围: {apps[0]['appid']} - {last_appid}), 本批找到 {batch_found} 个目标应用")
                
                # 检查是否还有更多数据
                have_more_results = data.get('have_more_results', False)
                if not have_more_results:
                    print(f"已到达Steam应用库末尾")
                    break
                
                # 优化：如果当前批次的最小appid已经大于目标最大appid，说明目标都已超过范围
                if apps[0]['appid'] > max_appid:
                    print(f"当前批次最小appid ({apps[0]['appid']}) 已超过目标最大appid ({max_appid})，停止查询")
                    break
                
                time.sleep(0.3)  # 限流
            
            print(f"查询完成，找到 {len(found_ids)}/{len(app_id_set)} 个应用")
            
            # 如果有遗漏的appid，尝试通过Store API补充
            missing_ids = app_id_set - found_ids
            if missing_ids:
                print(f"尝试补充缺失的 {len(missing_ids)} 个应用...")
                for appid in sorted(missing_ids):
                    try:
                        store_url = "https://store.steampowered.com/api/appdetails"
                        store_params = {
                            "appids": appid,
                            "l": "schinese",
                            "cc": "cn"
                        }
                        store_resp = requests.get(store_url, params=store_params, timeout=5)
                        if store_resp.status_code == 200:
                            store_data = store_resp.json()
                            if str(appid) in store_data and store_data[str(appid)].get('success'):
                                data = store_data[str(appid)].get('data', {})
                                app_info_map[str(appid)] = {
                                    'appid': appid,
                                    'name': data.get('name', 'Unknown')
                                }
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Failed to get app {appid} from Store API: {e}")
                        
        except Exception as e:
            print(f"Steam API Error (get_apps_info): {e}")
            
        return app_info_map

    def get_wishlist_app(self, steam_id):
        """
        获取愿望单中的应用ID列表
        使用 IWishlistService.GetWishlist 接口获取愿望单应用ID列表
        
        返回:
            app_ids: 愿望单中的应用ID列表
        """
        self._ensure_api()
        app_ids = []
        
        if self.api:
            try:
                response = self.api.IWishlistService.GetWishlist(steamid=steam_id)
                items = response.get('response', {}).get('items', [])
                app_ids = [item['appid'] for item in items]
            except Exception as e:
                print(f"Steam API Error (GetWishlistApp): {e}")
        return app_ids
    
    def get_game_followed(self, steam_id):
        """
        获取关注游戏的应用ID列表
        使用 IStoreService.GetGamesFollowed 接口获取关注游戏ID列表
        
        返回:
            app_ids: 关注游戏的应用ID列表
        """
        self._ensure_api()
        app_ids = []
        
        if self.api:
            try:
                response = self.api.IStoreService.GetGamesFollowed(steamid=steam_id)
                app_ids = response.get('response', {}).get('appids', [])
            except Exception as e:
                print(f"Steam API Error (GetGamesFollowedApp): {e}")
        return app_ids
    
    def get_wishlist(self, steam_id):
        """
        获取愿望单数据，并转换为 SteamWorker 期望的格式
        优先使用 IWishlistService 获取列表 + Store API 获取价格
        """
        self._ensure_api()
        
        app_ids1 = self.get_wishlist_app(steam_id)
        app_ids2 = self.get_game_followed(steam_id)
        app_ids = list(set(app_ids1 + app_ids2))

        # 如果拿到了 AppID，去商店查价格并转换格式
        if app_ids:
            wishlist_dict = {}
            import time
            
            # 2.1 获取基本信息 (Name) - 使用 IStoreService (WebAPI)
            app_info_map = self.get_apps_info(app_ids)

            # 2.2 获取价格 (Store API)
            # 分批查询，每次 50 个
            chunk_size = 50
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
