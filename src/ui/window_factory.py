from src.ui.settings_dialog import SettingsDialog
from src.ui.stats_window import StatsWindow
from src.ui.discount_window import DiscountWindow
from src.ui.all_games_window import AllGamesWindow
from src.ui.achievement_window import AchievementWindow
from src.ui.reminder_settings_window import ReminderSettingsWindow

class WindowFactory:
    """
    窗口工厂
    负责创建各种子窗口，封装依赖注入细节
    """
    def __init__(self, steam_manager, config_manager, timer_handler):
        self.steam_manager = steam_manager
        self.config_manager = config_manager
        self.timer_handler = timer_handler

    def create_reminder_settings_window(self, parent=None):
        """
        创建提醒设置窗口
        """
        return ReminderSettingsWindow(self.timer_handler, parent=parent)

    def create_settings_dialog(self):
        window = SettingsDialog()
        
        # 1. 加载配置
        window.load_settings(self.config_manager.settings)
        
        # 2. 处理保存请求
        def handle_save(settings):
            for key, value in settings.items():
                self.config_manager.set(key, value)
            
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
            
        def on_games_updated(data):
            pass
        window.request_search_games.connect(handle_search)
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


