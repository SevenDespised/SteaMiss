from PyQt6.QtCore import QPoint
from src.ui.radial_menu import RadialMenu
from src.logic.menu_builders.path_builder import PathMenuBuilder
from src.logic.menu_builders.interaction_builder import InteractionMenuBuilder
from src.logic.menu_builders.timer_builder import TimerMenuBuilder
from src.logic.menu_builders.steam_game_builder import SteamGameMenuBuilder
from src.logic.menu_builders.tool_builder import ToolMenuBuilder


class UIManager:
    """
    UI管理器
    负责协调各个菜单项构建器，生成环形菜单
    """
    
    def __init__(self, tool_manager, steam_manager, config_manager):
        self.tool_manager = tool_manager
        self.steam_manager = steam_manager
        self.config_manager = config_manager
        
        # 管理的 UI 组件
        self.radial_menu = RadialMenu()
        
        # 初始化各个菜单项构建器
        self.path_builder = PathMenuBuilder(tool_manager, config_manager)
        self.interaction_builder = InteractionMenuBuilder(tool_manager, config_manager)
        self.timer_builder = TimerMenuBuilder(tool_manager, config_manager)
        self.steam_game_builder = SteamGameMenuBuilder(tool_manager, config_manager, steam_manager)
        self.tool_builder = ToolMenuBuilder(tool_manager, config_manager)
        
    def get_radial_menu(self):
        """提供给 Pet 用于事件连接 (如 hover)"""
        return self.radial_menu

    def show_radial_menu(self, center_pos: QPoint):
        """
        构建并显示环形菜单
        """
        # 1. 获取菜单项数据
        items = self._build_menu_items()
        
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

    def _build_menu_items(self):
        """
        内部方法：构建排序好的菜单项列表
        使用各个专门的构建器来生成菜单项
        """
        # 定义排序顺序
        order = [
            "say_hello", "launch_recent", "discounts",
            "timer", "stats", "launch_favorite", "open_path"
        ]
        
        # 收集所有菜单项
        all_items = []
        
        # 1. 路径打开
        all_items.append(self.path_builder.build())
        
        # 2. 交互功能
        all_items.append(self.interaction_builder.build())
        
        # 3. 工具类
        all_items.append(self.tool_builder.build_stats_item())
        # 4. 计时器
        all_items.append(self.timer_builder.build())
        
        # 5. Steam 游戏
        recent_item = self.steam_game_builder.build_recent_game_item()
        if recent_item:
            all_items.append(recent_item)
        
        quick_launch_item = self.steam_game_builder.build_quick_launch_item()
        if quick_launch_item:
            all_items.append(quick_launch_item)
        
        # 排序并填充空位
        items_map = {item['key']: item for item in all_items}
        sorted_items = []
        for key in order:
            if key in items_map:
                sorted_items.append(items_map[key])
            else:
                # 填充空项，保持扇区数量固定
                sorted_items.append(None)
        
        return sorted_items