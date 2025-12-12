from src.ui.settings_dialog import SettingsDialog
from src.ui.stats_window import StatsWindow
from src.ui.discount_window import DiscountWindow
from src.ui.all_games_window import AllGamesWindow
from src.ui.achievement_window import AchievementWindow

class WindowFactory:
    """
    窗口工厂
    负责创建各种子窗口，封装依赖注入细节
    """
    def __init__(self, steam_manager, config_manager):
        self.steam_manager = steam_manager
        self.config_manager = config_manager

    def create_settings_dialog(self):
        window = SettingsDialog()
        
        # 1. 加载配置
        window.load_settings(self.config_manager.settings)
        
        # 2. 处理保存请求
        def handle_save(settings):
            for key, value in settings.items():
                self.config_manager.set(key, value)
            # 可能需要触发一些更新，比如重新加载 Steam 数据
            # 但 ConfigManager 可能会自动处理，或者由其他组件监听 Config 变化
            
        window.request_save.connect(handle_save)
        
        # 3. 处理游戏搜索请求
        def handle_search(keyword):
            results = self.steam_manager.search_games(keyword)
            if not results:
                # 如果没搜到，尝试触发更新
                # 这里逻辑稍微复杂一点，因为 fetch 是异步的
                # 我们可以在这里连接一次性信号，或者让 UI 显示“正在更新”
                # 为了简单，我们先返回空，并触发更新
                self.steam_manager.fetch_games_stats()
            window.update_search_results(results)
            
        # 为了支持“更新后自动刷新搜索结果”，我们需要让 Window 也能响应数据更新
        def on_games_updated(data):
            # 如果窗口还开着，且有搜索关键词（这个状态在 UI 里），
            # 我们可以再次触发搜索。
            # 但由于这是被动视图，Window 不应该自己决定逻辑。
            # 我们可以简单地通知 Window 数据更新了，让它自己决定是否重试搜索
            # 或者，我们在 Window 里保留了 refresh_search_results 逻辑？
            # 不，Window 里已经移除了 steam_manager 依赖。
            # 所以，我们需要在这里处理。
            # 简单起见，我们只处理同步搜索。如果需要异步更新后搜索，
            # 用户可以再次点击搜索按钮。
            pass
        window.request_search_games.connect(handle_search)
        # 额外：如果 Steam 数据更新了，可能需要刷新搜索结果（如果用户正在搜索）
        # 这里为了简化，暂不自动刷新搜索结果，依靠用户手动重试。
        return window

    def create_stats_window(self):
        window = StatsWindow()
        
        # 定义数据更新闭包
        def update_window_data():
            datasets = self.steam_manager.get_game_datasets()
            fallback_summary = self.steam_manager.cache.get("summary") if self.steam_manager.cache else None
            # 假设 steam_manager.config 是个 dict
            window.update_data(datasets, fallback_summary, self.steam_manager.config)

        # 连接数据源信号 -> 更新 UI
        self.steam_manager.on_player_summary.connect(update_window_data)
        self.steam_manager.on_games_stats.connect(update_window_data)
        
        # 连接 UI 请求 -> 数据源动作
        window.request_refresh.connect(self.steam_manager.fetch_player_summary)
        window.request_refresh.connect(self.steam_manager.fetch_games_stats)
        
        # 初始加载数据
        update_window_data()
        
        return window

    def create_all_games_window(self):
        window = AllGamesWindow()
        
        def update_window_data():
            datasets = self.steam_manager.get_game_datasets()
            prices = self.steam_manager.cache.get("prices", {})
            window.update_data(datasets, prices=prices)
            
        # 连接数据源信号
        self.steam_manager.on_games_stats.connect(update_window_data)
        self.steam_manager.on_store_prices.connect(update_window_data)
        
        # 连接 UI 请求
        window.request_fetch_prices.connect(self.steam_manager.fetch_store_prices)
        
        # 初始加载
        update_window_data()
        
        return window

    def create_achievement_window(self):
        window = AchievementWindow()
        
        def update_window_data():
            datasets = self.steam_manager.get_game_datasets()
            achievements = self.steam_manager.cache.get("achievements", {})
            window.update_data(datasets, achievements=achievements)
            
        # 连接数据源信号
        self.steam_manager.on_games_stats.connect(update_window_data)
        self.steam_manager.on_achievements_data.connect(update_window_data)
        
        # 连接 UI 请求
        window.request_fetch_achievements.connect(self.steam_manager.fetch_achievements)
        
        # 初始加载
        update_window_data()
        
        return window

    def create_discount_window(self):
        window = DiscountWindow()
        
        def update_window_data(games):
            window.update_data(games)
            
        # 连接数据源信号
        self.steam_manager.on_wishlist_data.connect(update_window_data)
        
        # 连接 UI 请求
        window.request_refresh.connect(self.steam_manager.fetch_wishlist)
        
        # 初始加载
        if "wishlist" in self.steam_manager.cache:
            update_window_data(self.steam_manager.cache["wishlist"])
        else:
            # 如果没有缓存，自动触发一次刷新
            self.steam_manager.fetch_wishlist()
            
        return window


