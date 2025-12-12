from src.ui.settings_dialog import SettingsDialog
from src.ui.stats_window import StatsWindow
from src.ui.discount_window import DiscountWindow
from src.ui.all_games_window import AllGamesWindow

class WindowFactory:
    """
    窗口工厂
    负责创建各种子窗口，封装依赖注入细节
    """
    def __init__(self, steam_manager, config_manager):
        self.steam_manager = steam_manager
        self.config_manager = config_manager

    def create_settings_dialog(self):
        return SettingsDialog(self.config_manager, self.steam_manager)

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
            window.update_data(datasets, prices)
            
        # 连接数据源信号
        self.steam_manager.on_games_stats.connect(update_window_data)
        self.steam_manager.on_store_prices.connect(update_window_data)
        
        # 连接 UI 请求
        window.request_fetch_prices.connect(self.steam_manager.fetch_store_prices)
        
        # 初始加载
        update_window_data()
        
        return window

    def create_discount_window(self):
        return DiscountWindow(self.steam_manager)


