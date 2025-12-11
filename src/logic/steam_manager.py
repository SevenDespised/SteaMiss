from PyQt6.QtCore import QObject, pyqtSignal
from src.logic.steam_support.steam_worker import SteamWorker
from src.logic.steam_support.steam_aggregator import GamesAggregator
import json
import os

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
        self.games_aggregator = GamesAggregator()
        
        # 1. 加载本地数据
        self.load_local_data()
        
        # 2. 如果配置齐全，尝试自动更新
        key, sid = self._get_primary_credentials()
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

    def _get_primary_credentials(self, allow_alt_fallback=True):
        key = self.config.get("steam_api_key")
        sid = self.config.get("steam_id")

        if not sid and allow_alt_fallback:
            alt_ids = self.config.get("steam_alt_ids", [])
            if isinstance(alt_ids, list) and alt_ids:
                sid = alt_ids[0]

        return key, sid

    def _get_all_account_ids(self):
        ids = []
        primary = self.config.get("steam_id")
        if primary:
            ids.append(primary)

        alt_ids = self.config.get("steam_alt_ids", [])
        if isinstance(alt_ids, list):
            for sid in alt_ids:
                if sid and sid not in ids:
                    ids.append(sid)
        return ids

    def fetch_player_summary(self):
        """异步获取玩家信息"""
        key, sid = self._get_primary_credentials()
        self._start_worker(key, sid, "summary")

    def fetch_games_stats(self):
        """异步获取游戏统计"""
        key = self.config.get("steam_api_key")
        ids = self._get_all_account_ids()
        if not key or not ids:
            return

        primary_id = self.config.get("steam_id") or ids[0]
        self.games_aggregator.begin(ids, primary_id)

        for sid in ids:
            self._start_worker(key, sid, "games", steam_id=sid)

    def fetch_store_prices(self, appids):
        """异步获取游戏价格"""
        key, sid = self._get_primary_credentials()
        self._start_worker(key, sid, "store_prices", extra_data=appids)

    def fetch_wishlist(self):
        """异步获取愿望单折扣"""
        key, sid = self._get_primary_credentials()
        self._start_worker(key, sid, "wishlist")

    def get_recent_game(self):
        """从缓存中获取最近游玩的游戏"""
        games_cache = self._get_primary_games_cache()
        if games_cache and games_cache.get("recent_game"):
            return games_cache["recent_game"]
        return None

    def get_recent_games(self, limit=3):
        """
        获取最近游玩的游戏列表 (Top N)
        如果不足 N 个，则用其他游戏填充 (通过排序自动实现)
        """
        games_cache = self._get_primary_games_cache()
        if not games_cache or not games_cache.get("all_games"):
            return []
        
        all_games = games_cache["all_games"]
        # 按 rtime_last_played 降序
        sorted_games = sorted(all_games, key=lambda x: x.get('rtime_last_played', 0), reverse=True)
        
        return sorted_games[:limit]

    def search_games(self, keyword):
        """
        在缓存的游戏列表中搜索
        返回匹配的游戏列表 [{"name": "xxx", "appid": 123}, ...]
        """
        games_cache = self._get_primary_games_cache()
        if not games_cache or not games_cache.get("all_games"):
            return []

        keyword = keyword.lower()
        results = []
        for game in games_cache["all_games"]:
            name = game.get("name", "").lower()
            if keyword in name:
                results.append(game)
        return results

    def _start_worker(self, key, sid, task_type, extra_data=None, steam_id=None):
        # 简单的任务队列机制
        # 如果当前有 worker 在运行，我们不能直接 return，否则并发请求会丢失
        # 这里我们简单地创建新的 worker 实例来处理并发请求
        # 注意：这可能会导致多个线程同时运行，对于简单的应用是可以接受的
        # 更好的做法是实现一个任务队列，但为了保持代码简单，我们允许并发
        
        worker = SteamWorker(key, steam_id or sid, task_type, extra_data)
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
            # 确保多账号任务不会因为单个账号失败而卡住
            if result["type"] == "games" and self.games_aggregator:
                done = self.games_aggregator.mark_error()
                if done:
                    self._finalize_games_results()

            self.on_error.emit(result["error"])
            return

        task_type = result["type"]
        data = result["data"]
        
        if data is None:
            return

        if task_type == "summary":
            self.cache["summary"] = data
            self.on_player_summary.emit(data)
        elif task_type == "games":
            if self.games_aggregator:
                done = self.games_aggregator.add_result(result.get("steam_id"), data)
                if done:
                    self._finalize_games_results()
            else:
                # 兼容单账号模式
                self.cache["games"] = data
                self.cache["games_primary"] = data
                self.on_games_stats.emit(data)
                self.save_local_data()
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
        if task_type != "games":
            self.save_local_data()

    def _finalize_games_results(self):
        primary_data, aggregated = self.games_aggregator.finalize()

        if primary_data:
            self.cache["games_primary"] = primary_data

        if aggregated:
            self.cache["games"] = aggregated
            self.on_games_stats.emit(aggregated)
            self.save_local_data()

    def _get_primary_games_cache(self):
        if "games_primary" in self.cache:
            return self.cache["games_primary"]
        if "games" in self.cache:
            return self.cache["games"]
        return None
