from PyQt6.QtCore import QObject


class WindowHandler(QObject):
    """
    窗口管理器：负责管理子窗口生命周期（单例复用/激活/清理失效实例）。
    """

    def __init__(self, window_factory):
        super().__init__()
        self.window_factory = window_factory
        self.active_windows = {}

        # 注入导航回调，供 Binder 使用（例如 StatsWindow 内部跳转到 all_games）
        try:
            self.window_factory.set_navigator(self.open_window)
        except Exception:
            pass

    def open_window(self, window_name):
        """
        打开指定的工具窗口。
        @param window_name: 注册名（例如 'stats'/'all_games'）
        """
        if window_name in self.active_windows:
            window = self.active_windows[window_name]
            try:
                window.show()
                window.activateWindow()
                return
            except RuntimeError:
                del self.active_windows[window_name]

        new_window = self.window_factory.create_window(window_name)
        if new_window:
            self.active_windows[window_name] = new_window
            new_window.show()


__all__ = ["WindowHandler"]


