from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal
from src.utils.path_utils import resource_path

class TrayManager(QObject):
    """
    系统托盘管理器
    负责管理托盘图标、菜单以及相关动作
    """
    request_toggle_visibility = pyqtSignal()
    request_toggle_topmost = pyqtSignal()
    request_open_settings = pyqtSignal()
    request_quit_app = pyqtSignal()

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.tray_icon = None
        self.action_toggle = None
        self.action_topmost = None
        
        self._setup_tray()

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
        self.action_toggle.triggered.connect(self.request_toggle_visibility.emit)
        tray_menu.addAction(self.action_toggle)
        
        # 动作：取消置顶/置顶
        self.action_topmost = QAction("取消置顶", self.app)
        self.action_topmost.triggered.connect(self.request_toggle_topmost.emit)
        tray_menu.addAction(self.action_topmost)
        
        # 动作：设置
        action_settings = QAction("功能设置", self.app)
        action_settings.triggered.connect(self.request_open_settings.emit)
        tray_menu.addAction(action_settings)
        
        tray_menu.addSeparator()
        
        # 动作：退出
        action_quit = QAction("退出", self.app)
        action_quit.triggered.connect(self.request_quit_app.emit)
        tray_menu.addAction(action_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def update_visibility_text(self, visible):
        if self.action_toggle:
            if visible:
                self.action_toggle.setText("隐藏宠物")
            else:
                self.action_toggle.setText("显示宠物")

    def update_topmost_text(self, is_topmost):
        if self.action_topmost:
            if is_topmost:
                self.action_topmost.setText("取消置顶")
            else:
                self.action_topmost.setText("置顶宠物")

    def show_message(self, title, message, icon=QSystemTrayIcon.MessageIcon.NoIcon, duration=2000):
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, duration)
