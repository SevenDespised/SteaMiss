from src.ui.settings_dialog import SettingsDialog
from src.ui.stats_window import StatsWindow
from src.ui.discount_window import DiscountWindow

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
        return StatsWindow(self.steam_manager)

    def create_discount_window(self):
        return DiscountWindow(self.steam_manager)
