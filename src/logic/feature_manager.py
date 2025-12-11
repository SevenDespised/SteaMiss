from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
import os
import webbrowser

class FeatureManager(QObject):
    request_open_tool = pyqtSignal(str)
    request_hide_pet = pyqtSignal()
    request_toggle_topmost = pyqtSignal()
    request_say_hello = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, steam_manager=None, config_manager=None, timer_manager=None):
        super().__init__()
        self.steam_manager = steam_manager
        self.config_manager = config_manager
        self.timer_manager = timer_manager
        
        self._init_actions()

    def _init_actions(self):
        self.actions = {
            "say_hello": self.action_say_hello,
            "open_path": self.action_open_explorer,
            "hide_pet": self.action_hide_pet,
            "toggle_topmost": self.action_toggle_topmost,
            "exit": self.action_exit,
            "launch_game": self.action_launch_steam_game,
            "open_url": self.action_open_url,
            "open_steam_page": self.action_open_steam_page,
            "toggle_timer": self.action_toggle_timer,
            "pause_timer": self.action_pause_timer,
            "resume_timer": self.action_resume_timer,
            "stop_timer": self.action_stop_timer,
        }

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
        handler = self.actions.get(action_key)
        if handler:
            try:
                handler(**kwargs)
            except Exception as e:
                self.error_occurred.emit(f"Error executing {action_key}: {str(e)}")
        else:
            print(f"Unknown action: {action_key}")

    def action_say_hello(self, **kwargs):
        if not self.config_manager: return
        content = self.config_manager.get("say_hello_content", "你好！")
        self.request_say_hello.emit(content)

    def action_open_explorer(self, path=None, **kwargs):
        if not self.config_manager: return
        
        if path is None:
            # 默认使用第一个配置的路径
            paths = self.config_manager.get("explorer_paths", ["C:/"])
            path = paths[0] if paths else "C:/"
            
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                self.error_occurred.emit(f"Failed to open path {path}: {e}")
        else:
            self.error_occurred.emit(f"Path not found: {path}")

    def action_launch_steam_game(self, appid=None, **kwargs):
        if not appid: return
        try:
            os.startfile(f"steam://run/{appid}")
        except Exception as e:
            self.error_occurred.emit(f"Failed to launch game {appid}: {e}")

    def action_open_url(self, url=None, **kwargs):
        if not url: return
        try:
            webbrowser.open(url)
        except Exception as e:
            self.error_occurred.emit(f"Failed to open URL {url}: {e}")

    def action_open_steam_page(self, page_type=None, **kwargs):
        """
        page_type: 'library', 'community', 'store', 'workshop'
        """
        steam_commands = {
            'store': 'steam://store',
            'community': 'steam://url/CommunityHome',
            'library': 'steam://nav/games',
            'workshop': 'steam://url/SteamWorkshop'
        }
        
        web_urls = {
            'store': 'https://store.steampowered.com/',
            'community': 'https://steamcommunity.com/',
            'library': 'https://steamcommunity.com/my/games',
            'workshop': 'https://steamcommunity.com/workshop/'
        }
        
        cmd = steam_commands.get(page_type)
        url = web_urls.get(page_type)
        
        if cmd:
            try:
                os.startfile(cmd)
            except Exception as e:
                if url:
                    self.action_open_url(url=url)
                else:
                    self.error_occurred.emit(f"Failed to open steam command {cmd}: {e}")
        elif url:
            self.action_open_url(url=url)

    def action_toggle_timer(self, **kwargs):
        if not self.timer_manager:
            self.error_occurred.emit("TimerManager not configured")
            return
        running = self.timer_manager.toggle()
        state = "START" if running else "STOP"
        print(f"Timer state: {state}")

    def action_pause_timer(self, **kwargs):
        if self.timer_manager:
            self.timer_manager.pause()
            print("Timer paused")

    def action_resume_timer(self, **kwargs):
        if self.timer_manager:
            self.timer_manager.resume()
            print("Timer resumed")

    def action_stop_timer(self, **kwargs):
        if self.timer_manager:
            self.timer_manager.stop_and_persist()
            print("Timer stopped and saved")

    def action_hide_pet(self, **kwargs):
        self.request_hide_pet.emit()

    def action_toggle_topmost(self, **kwargs):
        self.request_toggle_topmost.emit()
        
    def action_exit(self, **kwargs):
        QApplication.instance().quit()


    def open_tool(self, tool_name):
        """
        打开指定的工具，如果已打开则激活
        """
        self.request_open_tool.emit(tool_name)
