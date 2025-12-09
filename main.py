import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QIcon, QAction
from src.pet import DesktopPet
from src.ui.settings_dialog import SettingsDialog

def main():
    app = QApplication(sys.argv)
    
    # 防止最后一个窗口关闭时退出程序
    app.setQuitOnLastWindowClosed(False)
    
    # --- 托盘图标设置 ---
    tray_icon = QSystemTrayIcon(app)
    
    icon = QIcon("assets/icon.png")
    if icon.isNull():
        icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        
    tray_icon.setIcon(icon) 
    
    # 托盘菜单
    tray_menu = QMenu()
    
    # 1. 创建宠物实例 (提前创建以便后续使用)
    pet = DesktopPet()
    
    # 用于保持对设置窗口的引用，防止被垃圾回收
    settings_dialog = None

    # 2. 定义打开设置界面的函数
    def open_settings():
        nonlocal settings_dialog
        
        # 如果窗口已经打开，则直接激活它
        if settings_dialog is not None and settings_dialog.isVisible():
            settings_dialog.raise_()
            settings_dialog.activateWindow()
            return

        # 传入 pet.config_manager，确保设置界面修改的是同一份配置
        # 传入 pet.steam_manager，以便在设置界面进行游戏搜索
        settings_dialog = SettingsDialog(pet.config_manager, pet.steam_manager)
        # 使用 show() 而不是 exec()，这样是非模态的，不会阻塞主循环
        settings_dialog.show()
    
    action_settings = QAction("功能设置", app)
    action_settings.triggered.connect(open_settings)
    tray_menu.addAction(action_settings)
    
    tray_menu.addSeparator()
    
    action_quit = QAction("退出", app)
    action_quit.triggered.connect(app.quit)
    
    tray_menu.addAction(action_quit)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    # -------------------
    
    pet.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
