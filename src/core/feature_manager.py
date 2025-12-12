from PyQt6.QtCore import QObject, pyqtSignal

class FeatureManager(QObject):
    request_open_tool = pyqtSignal(str)
    request_hide_pet = pyqtSignal()
    request_toggle_topmost = pyqtSignal()
    request_say_hello = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, system_handler, steam_manager, timer_manager, pet_handler):
        super().__init__()
        self.system_handler = system_handler
        self.steam_manager = steam_manager
        self.timer_manager = timer_manager
        self.pet_handler = pet_handler
        
        self._init_actions()

    def _init_actions(self):
        self.actions = {
            # System
            "open_path": self.system_handler.open_explorer,
            "open_url": self.system_handler.open_url,
            "exit": self.system_handler.exit_app,
            
            # Steam
            "launch_game": self.steam_manager.launch_game,
            "open_steam_page": self.steam_manager.open_page,
            
            # Timer
            "toggle_timer": self.timer_manager.toggle,
            "pause_timer": self.timer_manager.pause,
            "resume_timer": self.timer_manager.resume,
            "stop_timer": self.timer_manager.stop_and_persist,
            
            # Pet (Special handling for signals)
            "say_hello": self._handle_say_hello,
            "hide_pet": self._handle_hide_pet,
            "toggle_topmost": self._handle_toggle_topmost,
        }

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

    def _handle_say_hello(self, **kwargs):
        content = self.pet_handler.say_hello(**kwargs)
        if content:
            self.request_say_hello.emit(content)

    def _handle_hide_pet(self, **kwargs):
        self.request_hide_pet.emit()

    def _handle_toggle_topmost(self, **kwargs):
        self.request_toggle_topmost.emit()

    def open_tool(self, tool_name):
        """
        打开指定的工具，如果已打开则激活
        """
        self.request_open_tool.emit(tool_name)

