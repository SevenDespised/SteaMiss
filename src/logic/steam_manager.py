from PyQt6.QtCore import QObject, QThread, pyqtSignal
from src.api.steam_client import SteamClient
import time
import json
import os

class SteamWorker(QThread):
    """
    后台工作线程，用于执行耗时的网络请求
    """
    data_ready = pyqtSignal(dict) # 信号：携带数据字典

    def __init__(self, api_key, steam_id, task_type="summary", extra_data=None):
        super().__init__()
        self.client = SteamClient(api_key)
        self.steam_id = steam_id
        self.task_type = task_type
        self.extra_data = extra_data # 用于传递额外参数，如 appids

    def run(self):
        result = {"type": self.task_type, "data": None, "error": None}
        
        if not self.client.api_key or not self.steam_id:
            result["error"] = "Missing API Key or Steam ID"
            self.data_ready.emit(result)
            return

        try:
            if self.task_type == "summary":
                # 获取玩家基本信息
                players = self.client.get_player_summaries(self.steam_id)
                # 获取等级
                level = self.client.get_steam_level(self.steam_id)
                
                if players:
                    data = players[0]
                    data['steam_level'] = level
                    result["data"] = data
            
            elif self.task_type == "games":
                # 获取游戏列表
                games_data = self.client.get_owned_games(self.steam_id)
                if games_data:
                    games = games_data.get('games', [])
                    # 1. 按总时长排序 (用于统计)
                    games_by_playtime = sorted(games, key=lambda x: x.get('playtime_forever', 0), reverse=True)
                    
                    # 2. 按最近游玩时间排序 (用于"最近游玩"功能)
                    # rtime_last_played 是 Unix 时间戳
                    games_by_recent = sorted(games, key=lambda x: x.get('rtime_last_played', 0), reverse=True)
                    
                    # 3. 最近两周游玩时长前5
                    games_by_2weeks = sorted(games, key=lambda x: x.get('playtime_2weeks', 0), reverse=True)
                    top_2weeks = [g for g in games_by_2weeks if g.get('playtime_2weeks', 0) > 0][:5]

                    result["data"] = {
                        "count": games_data.get('game_count', 0),
                        "all_games": games, # 保存完整列表用于搜索
                        "top_games": games_by_playtime[:5],
                        "recent_game": games_by_recent[0] if games_by_recent else None,
                        "top_2weeks": top_2weeks,
                        "total_playtime": sum(g.get('playtime_forever', 0) for g in games)
                    }
                else:
                    result["error"] = "Failed to fetch games data (API returned None)"

            elif self.task_type == "store_prices":
                # 批量获取价格
                appids = self.extra_data
                if appids:
                    # 分批处理，每次 20 个，避免 URL 过长或超时
                    chunk_size = 20
                    all_prices = {}
                    for i in range(0, len(appids), chunk_size):
                        chunk = appids[i:i+chunk_size]
                        prices = self.client.get_app_details(chunk)
                        if prices:
                            all_prices.update(prices)
                        time.sleep(0.5) # 礼貌性延迟，防止被封 IP
                    result["data"] = all_prices

            elif self.task_type == "inventory":
                # 获取库存 (CS2)
                inv_data = self.client.get_player_inventory(self.steam_id, 730, 2)
                if inv_data and 'assets' in inv_data:
                    result["data"] = {
                        "total_items": len(inv_data['assets']),
                        # 这里可以做更多复杂的价值计算，暂时只返回数量
                    }

            elif self.task_type == "wishlist":
                # 获取愿望单
                wishlist_data = self.client.get_wishlist(self.steam_id)
                if wishlist_data:
                    discounted_games = []
                    for appid, details in wishlist_data.items():
                        # 必须是可购买的
                        subs = details.get('subs', [])
                        if not subs: continue
                        
                        # 寻找最大折扣
                        best_sub = None
                        max_discount = -1
                        
                        for sub in subs:
                            # discount_pct 有时是 null 或 0
                            discount = sub.get('discount_pct', 0) or 0
                            if discount > max_discount:
                                max_discount = discount
                                best_sub = sub
                        
                        # 只要有折扣就加入 (max_discount > 0)
                        if best_sub and max_discount > 0:
                            # 价格通常是格式化好的字符串，如 "¥ 38"
                            price_str = best_sub.get('price', '')
                            # 封面图
                            image_url = details.get('capsule', '')
                            
                            discounted_games.append({
                                "appid": appid,
                                "name": details.get('name', 'Unknown'),
                                "discount_pct": max_discount,
                                "price": price_str,
                                "image": image_url
                            })
                    
                    # 按折扣力度降序排序
                    discounted_games.sort(key=lambda x: x['discount_pct'], reverse=True)
                    
                    # 取前 10 个
                    result["data"] = discounted_games[:10]
                else:
                    # 如果获取失败或为空，返回空列表而不是报错，避免 UI 异常
                    result["data"] = []
                    
        except Exception as e:
            result["error"] = str(e)
            
        self.data_ready.emit(result)


class SteamManager(QObject):
    """
    业务逻辑管理器
    负责协调 UI 和 Worker，管理数据缓存
    """
    # 定义一些信号供 UI 连接
    on_player_summary = pyqtSignal(dict)
    on_games_stats = pyqtSignal(dict)
    on_store_prices = pyqtSignal(dict) # 商店价格信号
    on_wishlist_data = pyqtSignal(list) # 愿望单数据信号
    on_error = pyqtSignal(str)

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.cache = {}
        self.worker = None
        self.data_file = "config/steam_data.json"
        
        # 1. 加载本地数据
        self.load_local_data()
        
        # 2. 如果配置齐全，尝试自动更新
        key, sid = self._get_credentials()
        if key and sid:
            # 延迟一点启动，避免拖慢启动速度
            # 这里直接调用，因为 Worker 是异步的
            self.fetch_games_stats()
            self.fetch_player_summary()

    def load_local_data(self):
        """加载本地缓存数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"Loaded local steam data from {self.data_file}")
            except Exception as e:
                print(f"Failed to load local steam data: {e}")

    def save_local_data(self):
        """保存缓存数据到本地"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            print(f"Saved steam data to {self.data_file}")
        except Exception as e:
            print(f"Failed to save local steam data: {e}")

    def _get_credentials(self):
        return self.config.get("steam_api_key"), self.config.get("steam_id")

    def fetch_player_summary(self):
        """异步获取玩家信息"""
        key, sid = self._get_credentials()
        self._start_worker(key, sid, "summary")

    def fetch_games_stats(self):
        """异步获取游戏统计"""
        key, sid = self._get_credentials()
        self._start_worker(key, sid, "games")

    def fetch_store_prices(self, appids):
        """异步获取游戏价格"""
        key, sid = self._get_credentials()
        self._start_worker(key, sid, "store_prices", extra_data=appids)

    def fetch_wishlist(self):
        """异步获取愿望单折扣"""
        key, sid = self._get_credentials()
        self._start_worker(key, sid, "wishlist")

    def get_recent_game(self):
        """从缓存中获取最近游玩的游戏"""
        if "games" in self.cache and self.cache["games"].get("recent_game"):
            return self.cache["games"]["recent_game"]
        return None

    def search_games(self, keyword):
        """
        在缓存的游戏列表中搜索
        返回匹配的游戏列表 [{"name": "xxx", "appid": 123}, ...]
        """
        if "games" not in self.cache or not self.cache["games"].get("all_games"):
            return []
        
        keyword = keyword.lower()
        results = []
        for game in self.cache["games"]["all_games"]:
            name = game.get("name", "").lower()
            if keyword in name:
                results.append(game)
        return results

    def _start_worker(self, key, sid, task_type, extra_data=None):
        # 简单的任务队列机制
        # 如果当前有 worker 在运行，我们不能直接 return，否则并发请求会丢失
        # 这里我们简单地创建新的 worker 实例来处理并发请求
        # 注意：这可能会导致多个线程同时运行，对于简单的应用是可以接受的
        # 更好的做法是实现一个任务队列，但为了保持代码简单，我们允许并发
        
        worker = SteamWorker(key, sid, task_type, extra_data)
        worker.data_ready.connect(self._handle_worker_result)
        
        # 我们需要保持对 worker 的引用，防止被垃圾回收
        # 可以使用一个列表来管理所有活跃的 worker
        if not hasattr(self, 'active_workers'):
            self.active_workers = []
            
        self.active_workers.append(worker)
        
        # 当 worker 完成时，从列表中移除
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        
        worker.start()

    def _cleanup_worker(self, worker):
        if hasattr(self, 'active_workers') and worker in self.active_workers:
            self.active_workers.remove(worker)

    def _handle_worker_result(self, result):
        if result["error"]:
            self.on_error.emit(result["error"])
            # 即使出错，如果本地有旧数据，也可以考虑通知 UI 使用旧数据
            # 但目前的逻辑是 UI 直接查 cache，所以只要 cache 里有旧数据，UI 就能查到
            return

        task_type = result["type"]
        data = result["data"]

        if task_type == "summary":
            self.cache["summary"] = data
            self.on_player_summary.emit(data)
        elif task_type == "games":
            self.cache["games"] = data
            self.on_games_stats.emit(data)
        elif task_type == "store_prices":
            # 合并价格数据到缓存
            if "prices" not in self.cache:
                self.cache["prices"] = {}
            self.cache["prices"].update(data)
            self.on_store_prices.emit(data)
        elif task_type == "wishlist":
            self.cache["wishlist"] = data
            self.on_wishlist_data.emit(data)
            
        # 每次更新成功后，保存到本地
        self.save_local_data()
