from PyQt6.QtCore import QPoint, QObject, pyqtSignal
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QStyle, QApplication
from PyQt6.QtGui import QIcon, QAction
from src.utils.path_utils import resource_path
from src.ui.radial_menu import RadialMenu
from src.ui.settings_dialog import SettingsDialog
from src.ui.stats_window import StatsWindow
from src.ui.discount_window import DiscountWindow
from src.feature.menu_builders.path_builder import PathMenuBuilder
from src.feature.menu_builders.interaction_builder import InteractionMenuBuilder
from src.feature.menu_builders.timer_builder import TimerMenuBuilder
from src.feature.menu_builders.steam_game_builder import SteamGameMenuBuilder
from src.feature.menu_builders.tool_builder import ToolMenuBuilder


class UIManager(QObject):
    """
    UI管理器
    负责协调各个菜单项构建器，生成环形菜单
    负责管理所有子窗口的生命周期
    """
    
    menu_hovered_changed = pyqtSignal(int)

    def __init__(self, feature_manager, steam_manager, config_manager):
        super().__init__()
        self.feature_manager = feature_manager
        self.steam_manager = steam_manager
        self.config_manager = config_manager
        
        # 管理的 UI 组件
        self.radial_menu = RadialMenu()
        self.radial_menu.hovered_changed.connect(self.menu_hovered_changed)
        
        self.settings_dialog = None
        self.active_tools = {}
        self.tray_icon = None
        self.pet = None
        self.app = None
        
        # 初始化各个菜单项构建器
        self.path_builder = PathMenuBuilder(feature_manager, config_manager)
        self.interaction_builder = InteractionMenuBuilder(feature_manager, config_manager)
        self.timer_builder = TimerMenuBuilder(feature_manager, config_manager)
        self.steam_game_builder = SteamGameMenuBuilder(feature_manager, config_manager, steam_manager)
        self.tool_builder = ToolMenuBuilder(feature_manager, config_manager)
        
    def open_settings(self):
        """打开或激活设置窗口"""
        if self.settings_dialog is not None and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        # 懒加载：只有点击时才创建窗口
        self.settings_dialog = SettingsDialog(self.config_manager, self.steam_manager)
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
            new_tool = StatsWindow(self.steam_manager)
        elif tool_name == "discounts":
            new_tool = DiscountWindow(self.steam_manager)
            
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

    def setup_tray(self, app, pet):
        """初始化系统托盘"""
        self.app = app
        self.pet = pet
        self.tray_icon = QSystemTrayIcon(self.app)
        
        # 设置图标
        icon = QIcon(str(resource_path("assets", "icon.png")))
        if icon.isNull():
            icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        
        # 创建菜单
        tray_menu = QMenu()
        
        # 动作：显示/隐藏
        self.action_toggle = QAction("隐藏宠物", self.app)
        self.action_toggle.triggered.connect(self.toggle_pet_visibility)
        tray_menu.addAction(self.action_toggle)
        
        # 动作：取消置顶/置顶
        self.action_topmost = QAction("取消置顶", self.app)
        self.action_topmost.triggered.connect(self.toggle_topmost)
        tray_menu.addAction(self.action_topmost)
        
        # 动作：设置
        action_settings = QAction("功能设置", self.app)
        action_settings.triggered.connect(self.open_settings)
        tray_menu.addAction(action_settings)
        
        tray_menu.addSeparator()
        
        # 动作：退出
        action_quit = QAction("退出", self.app)
        action_quit.triggered.connect(self.quit_app)
        tray_menu.addAction(action_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def toggle_pet_visibility(self):
        # 使用 pet 的方法来切换，状态更新会通过信号回调
        if self.pet:
            self.pet.set_visibility(not self.pet.isVisible())

    def toggle_topmost(self):
        if self.pet:
            self.pet.toggle_topmost()

    def update_visibility_text(self, visible):
        if hasattr(self, 'action_toggle'):
            if visible:
                self.action_toggle.setText("隐藏宠物")
            else:
                self.action_toggle.setText("显示宠物")

    def update_topmost_text(self, is_topmost):
        if hasattr(self, 'action_topmost'):
            if is_topmost:
                self.action_topmost.setText("取消置顶")
            else:
                self.action_topmost.setText("置顶宠物")

    def quit_app(self):
        """安全退出程序"""
        if self.app:
            self.app.quit()

    def on_say_hello(self, content):
        """响应打招呼"""
        # 暂时使用托盘气泡显示，未来可以扩展为宠物气泡
        if self.tray_icon:
            self.tray_icon.showMessage("SteaMiss", content, QSystemTrayIcon.MessageIcon.NoIcon, 2000)
        print(f"[Pet Says]: {content}")

    def on_error_occurred(self, error_msg):
        """响应错误信息"""
        print(f"[Error]: {error_msg}")
        if self.tray_icon:
            self.tray_icon.showMessage("错误", error_msg, QSystemTrayIcon.MessageIcon.Warning, 3000)