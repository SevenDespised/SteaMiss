from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from src.pet import DesktopPet
from src.ui.timer_overlay import TimerOverlay

# 引入所有管理器
from src.core.config_manager import ConfigManager
from src.ai.behavior_manager import BehaviorManager
from src.feature.steam_manager import SteamManager
from src.feature.timer_manager import TimerManager
from src.core.feature_manager import FeatureManager
from src.core.resource_manager import ResourceManager
from src.core.ui_manager import UIManager
from src.feature.menu_composer import MenuComposer
from src.ui.window_factory import WindowFactory
from src.ui.tray_manager import TrayManager

from src.feature.handlers.system_handler import SystemFeatureHandler
from src.feature.handlers.steam_handler import SteamFeatureHandler
from src.feature.handlers.timer_handler import TimerFeatureHandler
from src.feature.handlers.pet_handler import PetFeatureHandler

class SteaMissApp:
    def __init__(self, app: QApplication):
        self.app = app
        
        # 1. 初始化所有服务 (依赖注入容器)
        self.config_manager = ConfigManager()
        self.behavior_manager = BehaviorManager()
        self.resource_manager = ResourceManager()
        self.timer_manager = TimerManager()
        self.steam_manager = SteamManager(self.config_manager)
        
        # 初始化 Feature Handlers
        self.system_handler = SystemFeatureHandler(self.config_manager)
        self.steam_handler = SteamFeatureHandler(self.steam_manager)
        self.timer_handler = TimerFeatureHandler(self.timer_manager)
        self.pet_handler = PetFeatureHandler(self.config_manager)
        
        self.feature_manager = FeatureManager(
            self.system_handler,
            self.steam_handler,
            self.timer_handler,
            self.pet_handler
        )
        
        # 初始化菜单组装器
        self.menu_composer = MenuComposer(
            self.feature_manager,
            self.steam_manager,
            self.config_manager,
            self.timer_manager
        )
        
        # 初始化窗口工厂
        self.window_factory = WindowFactory(
            self.steam_manager,
            self.config_manager
        )
        
        self.ui_manager = UIManager(
            self.menu_composer, 
            self.window_factory
        )
        
        # 初始化托盘管理器
        self.tray_manager = TrayManager(self.app)

        # 初始化 TimerOverlay (View Helper)
        self.timer_overlay = TimerOverlay(self.timer_manager)

        # 2. 初始化核心组件 (注入依赖)
        self.pet = DesktopPet(
            behavior_manager=self.behavior_manager,
            resource_manager=self.resource_manager,
            ui_manager=self.ui_manager,
            timer_manager=self.timer_manager,
            feature_manager=self.feature_manager,
            timer_overlay=self.timer_overlay
        )
        
        # 3. 初始化 UI 组件引用
        # self.tray_icon = None # 移至 UIManager
        
        # 4. 设置托盘
        # self.ui_manager.setup_tray(self.app) # 移至 TrayManager
        
        # 5. 显示宠物
        self.pet.show()
        
        # 6. 连接信号以同步状态
        self.pet.visibility_changed.connect(self.tray_manager.update_visibility_text)
        self.pet.topmost_changed.connect(self.tray_manager.update_topmost_text)
        
        # 连接 TrayManager 的请求信号
        self.tray_manager.request_toggle_visibility.connect(self.toggle_pet_visibility)
        self.tray_manager.request_toggle_topmost.connect(self.pet.toggle_topmost)
        self.tray_manager.request_open_settings.connect(self.ui_manager.open_settings)
        self.tray_manager.request_quit_app.connect(self.quit_app)
        
        # 7. 连接 FeatureManager 信号
        self.feature_manager.request_open_tool.connect(self.ui_manager.open_tool)
        self.feature_manager.request_hide_pet.connect(self.toggle_pet_visibility)
        self.feature_manager.request_toggle_topmost.connect(self.pet.toggle_topmost)
        self.feature_manager.request_say_hello.connect(self.on_say_hello)
        self.feature_manager.error_occurred.connect(self.on_error_occurred)

    def on_say_hello(self, content):
        """响应打招呼"""
        self.tray_manager.show_message("SteaMiss", content)
        print(f"[Pet Says]: {content}")

    def on_error_occurred(self, error_msg):
        """响应错误信息"""
        print(f"[Error]: {error_msg}")
        self.tray_manager.show_message("错误", error_msg, QSystemTrayIcon.MessageIcon.Warning, 3000)

    def toggle_pet_visibility(self):
        self.pet.set_visibility(not self.pet.isVisible())

    def quit_app(self):
        self.app.quit()
