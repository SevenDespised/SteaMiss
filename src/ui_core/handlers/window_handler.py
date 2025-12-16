from PyQt6.QtCore import QObject

class WindowHandler(QObject):
    """
    窗口管理器
    负责管理所有子窗口的生命周期
    """
    def __init__(self, window_factory):
        super().__init__()
        self.window_factory = window_factory
        self.active_windows = {}

    def open_window(self, window_name):
        """打开指定的工具窗口"""
        if window_name in self.active_windows:
            window = self.active_windows[window_name]
            try:
                window.show()
                window.activateWindow()
                return
            except RuntimeError:
                del self.active_windows[window_name]

        new_window = None
        if window_name == "stats":
            new_window = self.window_factory.create_stats_window()
            # 连接 StatsWindow 的跳转信号
            new_window.request_open_all_games.connect(lambda: self.open_window("all_games"))
        elif window_name == "all_games":
            new_window = self.window_factory.create_all_games_window()
        elif window_name == "discounts":
            new_window = self.window_factory.create_discount_window()
        elif window_name == "achievements":
            new_window = self.window_factory.create_achievement_window()
        elif window_name == "reminder_settings":
            new_window = self.window_factory.create_reminder_settings_window()
            
        if new_window:
            self.active_windows[window_name] = new_window
            new_window.show()
    