from src.feature.menu_builders.path_builder import PathMenuBuilder
from src.feature.menu_builders.interaction_builder import InteractionMenuBuilder
from src.feature.menu_builders.timer_builder import TimerMenuBuilder
from src.feature.menu_builders.steam_game_builder import SteamGameMenuBuilder
from src.feature.menu_builders.steam_page_builder import SteamPageMenuBuilder
from src.feature.menu_builders.tool_builder import ToolMenuBuilder
from src.feature.menu_builders.exit_builder import ExitMenuBuilder

class MenuComposer:
    """
    菜单组装器
    负责协调各个菜单项构建器，生成最终的菜单数据列表
    """
    def __init__(self, feature_router, steam_manager, config_manager, timer_handler):
        self.feature_router = feature_router
        self.steam_manager = steam_manager
        self.config_manager = config_manager
        self.timer_handler = timer_handler
        
        # 初始化各个菜单项构建器
        self.path_builder = PathMenuBuilder(feature_router, config_manager)
        self.interaction_builder = InteractionMenuBuilder(feature_router, config_manager)
        self.timer_builder = TimerMenuBuilder(feature_router, config_manager, timer_handler)
        self.steam_game_builder = SteamGameMenuBuilder(feature_router, config_manager, steam_manager)
        self.steam_page_builder = SteamPageMenuBuilder(feature_router, config_manager)
        self.tool_builder = ToolMenuBuilder(feature_router, config_manager)
        self.exit_builder = ExitMenuBuilder(feature_router, config_manager)

    def compose(self):
        """
        构建排序好的菜单项列表
        """
        # 定义排序顺序
        order = [
            "exit",
            "open_path",
            "open_steam_page",
            "stats",
            "timer",
            "launch_recent",
            "launch_favorite",
            "say_hello"
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
        
        # 6. Steam 页面
        steam_page_item = self.steam_page_builder.build()
        if steam_page_item:
            all_items.append(steam_page_item)
        
        # 7. 退出
        opts_item = self.exit_builder.build()
        if opts_item:
            all_items.append(opts_item)
        
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
