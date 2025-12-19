from PyQt6.QtCore import QObject
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QStyle, QSystemTrayIcon

from src.utils.path_utils import resource_path
from src.feature_core.app.actions import Action


class TrayHandler(QObject):
    """
    系统托盘管理器：负责托盘图标、菜单以及相关动作。
    """

    def __init__(self, action_bus, app):
        super().__init__()
        self.action_bus = action_bus
        self.app = app
        self.tray_icon = None
        self.action_toggle = None
        self.action_topmost = None
        self._setup_tray()

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app)

        icon = QIcon(str(resource_path("assets", "icon.png")))
        if icon.isNull():
            icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)

        tray_menu = QMenu()

        self.action_toggle = QAction("隐藏宠物", self.app)
        self.action_toggle.triggered.connect(lambda: self.action_bus.execute(Action.HIDE_PET))
        tray_menu.addAction(self.action_toggle)

        self.action_topmost = QAction("取消置顶", self.app)
        self.action_topmost.triggered.connect(lambda: self.action_bus.execute(Action.TOGGLE_TOPMOST))
        tray_menu.addAction(self.action_topmost)

        action_settings = QAction("功能设置", self.app)
        action_settings.triggered.connect(lambda: self.action_bus.execute(Action.OPEN_WINDOW, window_name="settings"))
        tray_menu.addAction(action_settings)

        tray_menu.addSeparator()

        action_quit = QAction("退出", self.app)
        action_quit.triggered.connect(lambda: self.action_bus.execute(Action.EXIT))
        tray_menu.addAction(action_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        """双击托盘图标时激活宠物窗口"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.action_bus.execute(Action.ACTIVATE_PET)

    def update_visibility_text(self, visible):
        if self.action_toggle:
            self.action_toggle.setText("隐藏宠物" if visible else "显示宠物")

    def update_topmost_text(self, is_topmost):
        if self.action_topmost:
            self.action_topmost.setText("取消置顶" if is_topmost else "置顶宠物")

    def show_message(self, title, message, icon=QSystemTrayIcon.MessageIcon.NoIcon, duration=2000):
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, duration)


__all__ = ["TrayHandler"]


