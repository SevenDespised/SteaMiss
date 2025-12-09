from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from src.ui.stats_window import StatsWindow
from src.ui.discount_window import DiscountWindow

class ToolManager:
    def __init__(self, steam_manager=None):
        self.active_tools = {}
        self.steam_manager = steam_manager

    def set_steam_manager(self, steam_manager):
        self.steam_manager = steam_manager

    def open_tool(self, tool_name):
        """
        打开指定的工具，如果已打开则激活
        """
        if tool_name in self.active_tools:
            window = self.active_tools[tool_name]
            # 如果窗口被关闭了（对象还在但不可见），重新显示
            # 注意：如果窗口被销毁了，这里可能会报错，需要处理 closeEvent
            try:
                window.show()
                window.activateWindow()
                return
            except RuntimeError:
                # 对象已被删除
                del self.active_tools[tool_name]

        # 工厂模式：根据名字创建对应的工具窗口
        new_tool = None
        if tool_name == "memo":
            # new_tool = self.create_memo_window()
            pass # 已移除
        elif tool_name == "stats":
            new_tool = self.create_stats_window()
        elif tool_name == "discounts":
            new_tool = self.create_discount_window()
            
        if new_tool:
            self.active_tools[tool_name] = new_tool
            new_tool.show()

    def create_stats_window(self):
        if not self.steam_manager:
            print("Error: SteamManager not initialized in ToolManager")
            return None
        return StatsWindow(self.steam_manager)

    def create_discount_window(self):
        if not self.steam_manager:
            return None
        return DiscountWindow(self.steam_manager)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("这是一个闹钟示例"))
        w.setLayout(layout)
        return w
