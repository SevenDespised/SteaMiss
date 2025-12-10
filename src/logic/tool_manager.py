from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from src.ui.stats_window import StatsWindow
from src.ui.discount_window import DiscountWindow
import os

class ToolManager:
    def __init__(self, steam_manager=None, config_manager=None, timer_manager=None):
        self.active_tools = {}
        self.steam_manager = steam_manager
        self.config_manager = config_manager
        self.timer_manager = timer_manager

    def set_steam_manager(self, steam_manager):
        self.steam_manager = steam_manager

    def set_config_manager(self, config_manager):
        self.config_manager = config_manager

    def set_timer_manager(self, timer_manager):
        self.timer_manager = timer_manager

    def execute_action(self, action_key, **kwargs):
        """
        执行非窗口类的动作
        """
        if action_key == "say_hello":
            self.action_say_hello()
        elif action_key == "open_path":
            self.action_open_explorer()
        elif action_key == "exit":
            QApplication.instance().quit()
        elif action_key == "launch_game":
            appid = kwargs.get("appid")
            if appid:
                self.action_launch_steam_game(appid)
        elif action_key == "toggle_timer":
            self.action_toggle_timer()
        elif action_key == "pause_timer":
            self.action_pause_timer()
        elif action_key == "resume_timer":
            self.action_resume_timer()
        elif action_key == "stop_timer":
            self.action_stop_timer()

    def action_say_hello(self):
        if not self.config_manager: return
        content = self.config_manager.get("say_hello_content", "你好！")
        print(content)
        # 这里未来可以扩展为显示气泡等

    def action_open_explorer(self):
        if not self.config_manager: return
        path = self.config_manager.get("explorer_path", "C:/")
        if os.path.exists(path):
            os.startfile(path)
        else:
            print(f"Path not found: {path}")

    def action_launch_steam_game(self, appid):
        try:
            os.startfile(f"steam://run/{appid}")
        except Exception as e:
            print(f"Failed to launch game {appid}: {e}")

    def action_toggle_timer(self):
        if not self.timer_manager:
            print("TimerManager not configured")
            return
        running = self.timer_manager.toggle()
        state = "START" if running else "STOP"
        print(f"Timer state: {state}")

    def action_pause_timer(self):
        if self.timer_manager:
            self.timer_manager.pause()
            print("Timer paused")

    def action_resume_timer(self):
        if self.timer_manager:
            self.timer_manager.resume()
            print("Timer resumed")

    def action_stop_timer(self):
        if self.timer_manager:
            self.timer_manager.stop_and_persist()
            print("Timer stopped and saved")

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