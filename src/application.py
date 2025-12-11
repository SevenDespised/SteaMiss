from PyQt6.QtWidgets import QApplication
from src.core.pet import DesktopPet
from src.ui.timer_overlay import TimerOverlay

# 引入所有管理器
from src.core.config_manager import ConfigManager
from src.ai.behavior_manager import BehaviorManager
from src.feature.steam_manager import SteamManager
from src.feature.timer_manager import TimerManager
from src.core.feature_manager import FeatureManager
from src.core.resource_manager import ResourceManager
from src.core.ui_manager import UIManager

class SteaMissApp:
    def __init__(self, app: QApplication):
        self.app = app
        
        # 1. 初始化所有服务 (依赖注入容器)
        self.config_manager = ConfigManager()
        self.behavior_manager = BehaviorManager()
        self.resource_manager = ResourceManager()
        self.timer_manager = TimerManager()
        self.steam_manager = SteamManager(self.config_manager)
        
        self.feature_manager = FeatureManager(
            self.steam_manager, 
            self.config_manager, 
            self.timer_manager
        )
        
        self.ui_manager = UIManager(
            self.feature_manager, 
            self.steam_manager, 
            self.config_manager
        )

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
        self.ui_manager.setup_tray(self.app, self.pet)
        
        # 5. 显示宠物
        self.pet.show()
        
        # 6. 连接信号以同步状态
        self.pet.visibility_changed.connect(self.ui_manager.update_visibility_text)
        self.pet.topmost_changed.connect(self.ui_manager.update_topmost_text)
        
        # 7. 连接 FeatureManager 信号
        self.feature_manager.request_open_tool.connect(self.ui_manager.open_tool)
        self.feature_manager.request_hide_pet.connect(self.ui_manager.toggle_pet_visibility)
        self.feature_manager.request_toggle_topmost.connect(self.ui_manager.toggle_topmost)
        self.feature_manager.request_say_hello.connect(self.ui_manager.on_say_hello)
        self.feature_manager.error_occurred.connect(self.ui_manager.on_error_occurred)
