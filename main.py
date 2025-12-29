import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.application import SteaMissApp
from src.utils.single_instance import ensure_single_instance
from src.utils.logging_config import install_global_exception_hooks, setup_logging

def main():
    # Initialize logging as early as possible (before Qt app starts)
    setup_logging()
    install_global_exception_hooks(logging.getLogger("steamiss"))

    # 检查单实例
    if not ensure_single_instance("SteaMiss"):
        # 已有实例在运行，显示提示后退出
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "SteaMiss 已在运行",
            "SteaMiss 已经在运行中！\n请在系统托盘查看。",
            QMessageBox.StandardButton.Ok
        )
        sys.exit(0)
    
    app = QApplication(sys.argv)
    
    # 防止最后一个窗口关闭时退出程序
    app.setQuitOnLastWindowClosed(False)
    
    # 初始化应用程序管理器
    manager = SteaMissApp(app)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
