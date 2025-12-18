from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QStyle, QSystemTrayIcon

from src.utils.path_utils import resource_path


class TrayHandler(QObject):
    """
    系统托盘管理器：负责托盘图标、菜单以及相关动作。
    """

    request_toggle_visibility = pyqtSignal()
    request_toggle_topmost = pyqtSignal()
    request_quit_app = pyqtSignal()
    request_activate_pet = pyqtSignal()

    def __init__(self, window_factory, app):
        super().__init__()
        self.window_factory = window_factory
        self.app = app
        self.tray_icon = None
        self.action_toggle = None
        self.action_topmost = None
        self.settings_dialog = None
        self._setup_tray()

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app)

        icon = QIcon(str(resource_path("assets", "icon.png")))
        if icon.isNull():
            icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)

        tray_menu = QMenu()

        self.action_toggle = QAction("隐藏宠物", self.app)
        self.action_toggle.triggered.connect(self.request_toggle_visibility.emit)
        tray_menu.addAction(self.action_toggle)

        self.action_topmost = QAction("取消置顶", self.app)
        self.action_topmost.triggered.connect(self.request_toggle_topmost.emit)
        tray_menu.addAction(self.action_topmost)

        action_settings = QAction("功能设置", self.app)
        action_settings.triggered.connect(self.open_settings)
        tray_menu.addAction(action_settings)

        tray_menu.addSeparator()

        action_quit = QAction("退出", self.app)
        action_quit.triggered.connect(self.request_quit_app.emit)
        tray_menu.addAction(action_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def open_settings(self):
        """打开或激活设置窗口"""
        if self.settings_dialog is not None and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        self.settings_dialog = self.window_factory.create_window("settings")
        self.settings_dialog.show()

    def on_tray_activated(self, reason):
        """双击托盘图标时激活宠物窗口"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.request_activate_pet.emit()

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


