from PyQt6.QtCore import QPoint, QObject, pyqtSignal
from src.ui.radial_menu import RadialMenu
# from src.ui.settings_dialog import SettingsDialog
# from src.ui.stats_window import StatsWindow
# from src.ui.discount_window import DiscountWindow
# from src.feature.menu_builders.path_builder import PathMenuBuilder
# from src.feature.menu_builders.interaction_builder import InteractionMenuBuilder
# from src.feature.menu_builders.timer_builder import TimerMenuBuilder
# from src.feature.menu_builders.steam_game_builder import SteamGameMenuBuilder
# from src.feature.menu_builders.tool_builder import ToolMenuBuilder


class UIManager(QObject):
    """
    UI管理器
    负责协调各个菜单项构建器，生成环形菜单
    负责管理所有子窗口的生命周期
    """
    
    menu_hovered_changed = pyqtSignal(int)
    
    # 托盘动作信号 - 移至 TrayManager
    # request_toggle_visibility = pyqtSignal()
    # request_toggle_topmost = pyqtSignal()
    # request_quit_app = pyqtSignal()

    def __init__(self, menu_composer, window_factory):
        super().__init__()
        self.menu_composer = menu_composer
        self.window_factory = window_factory
        
        # 管理的 UI 组件
        self.radial_menu = RadialMenu()
        self.radial_menu.hovered_changed.connect(self.menu_hovered_changed)
        
        self.settings_dialog = None
        self.active_tools = {}
        # self.tray_icon = None # 移至 TrayManager
        # self.pet = None # 移除直接依赖
        self.app = None
        
    def open_settings(self):
        """打开或激活设置窗口"""
        if self.settings_dialog is not None and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        # 懒加载：只有点击时才创建窗口
        self.settings_dialog = self.window_factory.create_settings_dialog()
        self.settings_dialog.show()

    def open_tool(self, tool_name):
        """打开指定的工具窗口"""
        if tool_name in self.active_tools:
            window = self.active_tools[tool_name]
            try:
                window.show()
                window.activateWindow()
                return
            except RuntimeError:
                del self.active_tools[tool_name]

        new_tool = None
        if tool_name == "stats":
            new_tool = self.window_factory.create_stats_window()
        elif tool_name == "discounts":
            new_tool = self.window_factory.create_discount_window()
            
        if new_tool:
            self.active_tools[tool_name] = new_tool
            new_tool.show()

    def handle_right_click(self, center_pos: QPoint):
        """
        处理右键点击事件：决定是显示还是关闭菜单
        """
        if self.is_radial_menu_just_closed():
            return

        if self.is_radial_menu_visible():
            self.close_radial_menu()
            return

        self.show_radial_menu(center_pos)
        
    def show_radial_menu(self, center_pos: QPoint):
        """
        构建并显示环形菜单
        """
        # 1. 获取菜单项数据
        items = self.menu_composer.compose()
        
        # 2. 设置并显示
        self.radial_menu.set_items(items)
        self.radial_menu.show_at(center_pos)

    def close_radial_menu(self):
        if self.radial_menu.isVisible():
            self.radial_menu.close()

    def is_radial_menu_visible(self):
        return self.radial_menu.isVisible()
        
    def is_radial_menu_just_closed(self):
        return getattr(self.radial_menu, 'just_closed', False)