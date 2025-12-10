from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QIcon, QAction
from src.pet import DesktopPet
from src.ui.settings_dialog import SettingsDialog

class AppManager:
    def __init__(self, app: QApplication):
        self.app = app
        
        # 1. 初始化核心组件
        self.pet = DesktopPet()
        
        # 2. 初始化 UI 组件引用
        self.tray_icon = None
        self.settings_dialog = None
        
        # 3. 设置托盘
        self._setup_tray()
        
        # 4. 显示宠物
        self.pet.show()

    def _setup_tray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self.app)
        
        # 设置图标
        icon = QIcon("assets/icon.png")
        if icon.isNull():
            icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        
        # 创建菜单
        tray_menu = QMenu()
        
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
