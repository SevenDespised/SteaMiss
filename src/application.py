from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from src.pet import DesktopPet
from src.ui.timer_overlay import TimerOverlay

# 引入所有管理器
from src.core.config_manager import ConfigManager
from src.ai.behavior_manager import BehaviorManager
from src.feature.steam_manager import SteamManager
from src.feature.handlers.timer_handler import TimerHandler
from src.core.feature_router import FeatureRouter
from src.core.resource_manager import ResourceManager
from src.core.ui_manager import UIManager
from src.feature.menu_composer import MenuComposer
from src.ui.window_factory import WindowFactory
from src.ui.tray_manager import TrayManager

from src.feature.handlers.system_handler import SystemFeatureHandler
# from src.feature.handlers.steam_handler import SteamFeatureHandler
# from src.feature.handlers.timer_handler import TimerFeatureHandler
from src.feature.handlers.pet_handler import PetFeatureHandler

class SteaMissApp:
    def __init__(self, app: QApplication):
        self.app = app
        
        # 1. 初始化所有服务 (依赖注入容器)
        self.config_manager = ConfigManager()
        self.behavior_manager = BehaviorManager()
        self.resource_manager = ResourceManager()
        self.timer_handler = TimerHandler(config_manager=self.config_manager)
        self.steam_manager = SteamManager(self.config_manager)
        
        # 初始化 Feature Handlers
        self.system_handler = SystemFeatureHandler(self.config_manager)
        self.pet_handler = PetFeatureHandler(self.config_manager)
        
        self.feature_router = FeatureRouter(
            self.system_handler,
            self.steam_manager,
            self.timer_handler,
            self.pet_handler
        )
        
        # 初始化菜单组装器
        self.menu_composer = MenuComposer(
            self.feature_router,
            self.steam_manager,
            self.config_manager,
            self.timer_handler
        )
        
        # 初始化窗口工厂
        self.window_factory = WindowFactory(
            self.steam_manager,
            self.config_manager,
            self.timer_handler
        )
        
        self.ui_manager = UIManager(
            self.menu_composer, 
            self.window_factory
        )
        
        # 初始化托盘管理器
        self.tray_manager = TrayManager(self.app)
        # 将托盘提醒作为计时提醒通知器
        self.timer_handler.set_notifier(self.tray_manager.show_message)
        # 退出时关闭计时器内部 Qt 定时器
        self.app.aboutToQuit.connect(self.timer_handler.shutdown)

        # 初始化 TimerOverlay (View Helper)
        self.timer_overlay = TimerOverlay(self.timer_handler)

        # 初始化核心组件 (注入依赖)
        self.pet = DesktopPet(
            behavior_manager=self.behavior_manager,
            resource_manager=self.resource_manager,
            timer_overlay=self.timer_overlay
        )
        
        # 显示宠物
        self.pet.show()
        
        # 连接信号以同步状态
        self.pet.visibility_changed.connect(self.tray_manager.update_visibility_text)
        self.pet.topmost_changed.connect(self.tray_manager.update_topmost_text)
        
        # 连接宠物交互信号
        self.pet.right_clicked.connect(self.ui_manager.handle_right_click)
        self.pet.double_clicked.connect(lambda: self.feature_router.execute_action("say_hello"))
        self.ui_manager.menu_hovered_changed.connect(self.pet.on_menu_hover_changed)
        
        # 连接 TrayManager 的请求信号
        self.tray_manager.request_toggle_visibility.connect(self.toggle_pet_visibility)
        self.tray_manager.request_toggle_topmost.connect(self.pet.toggle_topmost)
        self.tray_manager.request_open_settings.connect(self.ui_manager.open_settings)
        self.tray_manager.request_quit_app.connect(self.quit_app)
        self.tray_manager.request_activate_pet.connect(self.activate_pet)
        
        # 连接 FeatureRouter 信号
        self.feature_router.request_open_tool.connect(self.ui_manager.open_tool)
        self.feature_router.request_hide_pet.connect(self.toggle_pet_visibility)
        self.feature_router.request_toggle_topmost.connect(self.pet.toggle_topmost)
        self.feature_router.request_say_hello.connect(self.on_say_hello)
        self.feature_router.error_occurred.connect(self.on_error_occurred)

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
    
    def activate_pet(self):
        """
        激活宠物窗口：如果隐藏则显示，然后激活窗口获得焦点
        """
        if not self.pet.isVisible():
            self.pet.show()
        self.pet.activateWindow()
        self.pet.raise_()

    def quit_app(self):
        self.app.quit()
