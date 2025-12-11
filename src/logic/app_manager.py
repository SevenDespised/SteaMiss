from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QIcon, QAction
from src.utils.path_utils import resource_path
from src.pet import DesktopPet
from src.ui.settings_dialog import SettingsDialog
from src.ui.stats_window import StatsWindow
from src.ui.discount_window import DiscountWindow

class AppManager:
    def __init__(self, app: QApplication):
        self.app = app
        
        # 1. 初始化核心组件
        self.pet = DesktopPet()
        
        # 2. 初始化 UI 组件引用
        self.tray_icon = None
        self.settings_dialog = None
        self.active_tools = {}
        
        # 3. 设置托盘
        self._setup_tray()
        
        # 4. 显示宠物
        self.pet.show()
        
        # 5. 连接信号以同步状态
        self.pet.visibility_changed.connect(self.update_visibility_text)
        self.pet.topmost_changed.connect(self.update_topmost_text)
        
        # 6. 连接 FeatureManager 信号
        self.pet.feature_manager.request_open_tool.connect(self.on_open_tool_requested)
        self.pet.feature_manager.request_hide_pet.connect(self.toggle_pet_visibility)
        self.pet.feature_manager.request_toggle_topmost.connect(self.toggle_topmost)
        self.pet.feature_manager.request_say_hello.connect(self.on_say_hello)
        self.pet.feature_manager.error_occurred.connect(self.on_error_occurred)

    def _setup_tray(self):
        """初始化系统托盘"""
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
        self.pet.set_visibility(not self.pet.isVisible())

    def toggle_topmost(self):
        self.pet.toggle_topmost()

    def update_visibility_text(self, visible):
        if visible:
            self.action_toggle.setText("隐藏宠物")
        else:
            self.action_toggle.setText("显示宠物")

    def update_topmost_text(self, is_topmost):
        if is_topmost:
            self.action_topmost.setText("取消置顶")
        else:
            self.action_topmost.setText("置顶宠物")

    def open_settings(self):
        """打开或激活设置窗口"""
        if self.settings_dialog is not None and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        # 懒加载：只有点击时才创建窗口
        # 传入 pet.config_manager 和 pet.steam_manager
        self.settings_dialog = SettingsDialog(self.pet.config_manager, self.pet.steam_manager)
        self.settings_dialog.show()

    def quit_app(self):
        """安全退出程序"""
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

    def on_open_tool_requested(self, tool_name):
        """响应打开工具的请求"""
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
            new_tool = StatsWindow(self.pet.steam_manager)
        elif tool_name == "discounts":
            new_tool = DiscountWindow(self.pet.steam_manager)
            
        if new_tool:
            self.active_tools[tool_name] = new_tool
            new_tool.show()
