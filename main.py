import sys
from PyQt6.QtWidgets import QApplication
from src.logic.app_manager import AppManager

def main():
    app = QApplication(sys.argv)
    
    # 防止最后一个窗口关闭时退出程序
    app.setQuitOnLastWindowClosed(False)
    
    # 初始化应用程序管理器
    manager = AppManager(app)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
