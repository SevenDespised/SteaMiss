from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from src.ui.pet.pet import DesktopPet
from src.ui.widgets.timer_overlay import TimerOverlay

# 引入所有管理器
from src.storage.config_manager import ConfigManager
from src.ai.behavior_manager import BehaviorManager
from src.feature_core.adapters.qt.steam_facade_qt import SteamFacadeQt
from src.feature_core.adapters.qt.timer_facade_qt import TimerFacadeQt
from src.feature_core.adapters.qt.game_news_facade_qt import GameNewsFacadeQt
from src.storage.steam_repository import SteamRepository
from src.feature_core.adapters.qt.steam_task_service_qt import SteamTaskServiceQt
from src.feature_core.app.action_bus import ActionBus
from src.feature_core.app.actions import Action
from src.feature_core.app.ui_intents_qt import UiIntentsQt
from src.storage.resource_manager import ResourceManager
from src.ui.infra.handlers.window_handler import WindowHandler
from src.ui.infra.handlers.radial_handler import RadialHandler
from src.ui.infra.radial_composer.menu_composer import MenuComposer
from src.ui.infra.windowing.window_factory import WindowFactory
from src.ui.infra.handlers.tray_handler import TrayHandler
from src.ui.infra.radial_composer.menu_builders.exit_builder import ExitMenuBuilder
from src.ui.infra.radial_composer.menu_builders.interaction_builder import InteractionMenuBuilder
from src.ui.infra.radial_composer.menu_builders.path_builder import PathMenuBuilder
from src.ui.infra.radial_composer.menu_builders.steam_game_builder import SteamGameMenuBuilder
from src.ui.infra.radial_composer.menu_builders.steam_page_builder import SteamPageMenuBuilder
from src.ui.infra.radial_composer.menu_builders.timer_builder import TimerMenuBuilder
from src.ui.infra.radial_composer.menu_builders.tool_builder import ToolMenuBuilder

from src.feature_core.adapters.qt.system_facade_qt import SystemFacadeQt
from src.feature_core.services.pet_service import PetService
from src.feature_core.services.llm_service import LLMService
from src.storage.prompt_manager import PromptManager
from src.feature_core.adapters.qt.say_hello_facade_qt import SayHelloFacadeQt
from src.feature_core.services.steam.launcher_service import SteamLauncherService
import threading

class SteaMissApp:
    def __init__(self, app: QApplication):
        self.app = app
        
        # 1. 初始化所有服务 (依赖注入容器)
        self.config_manager = ConfigManager()
        self.behavior_manager = BehaviorManager()
        self.resource_manager = ResourceManager()
        self.timer_handler = TimerFacadeQt(config_manager=self.config_manager)
        self.steam_manager = SteamFacadeQt(
            self.config_manager,
            repository=SteamRepository(),
            task_service=SteamTaskServiceQt(),
        )
        self.news_manager = GameNewsFacadeQt()
        self.llm_service = LLMService(self.config_manager)
        self.prompt_manager = PromptManager()

        # ActionBus + UI intents
        self.ui_intents = UiIntentsQt()
        self.action_bus = ActionBus()
        
        # System/Pet：分别落在 adapters/qt 与 services
        self.system_facade = SystemFacadeQt(config_manager=self.config_manager)
        self.pet_service = PetService()

        # Steam launcher（纯业务）：生成可执行 URI/URL 计划；实际打开交给 SystemFacadeQt
        self.steam_launcher_service = SteamLauncherService()

        # SayHello：Qt 边界负责异步与 UI 信号驱动
        self.say_hello_facade = SayHelloFacadeQt(
            ui_intents=self.ui_intents,
            pet_service=self.pet_service,
            llm_service=self.llm_service,
            prompt_manager=self.prompt_manager,
            steam_manager=self.steam_manager,
        )

        def _emit_error(e: Exception, action: Action, kwargs: dict) -> None:
            self.ui_intents.error.emit(f"{action.value} failed: {e}")

        self.action_bus.set_error_handler(_emit_error)

        # 注册动作（Action -> handler）
        self.action_bus.register(Action.OPEN_PATH, self.system_facade.open_explorer)
        self.action_bus.register(Action.OPEN_URL, self.system_facade.open_url)
        self.action_bus.register(Action.EXIT, self.system_facade.exit_app)

        def _launch_game(appid=None, **_: object) -> None:
            plan = self.steam_launcher_service.build_launch_game(appid)
            if not plan:
                return
            self.system_facade.open_uri(uri=plan.primary_uri, fallback_url=plan.fallback_url)

        def _open_steam_page(page_type=None, **_: object) -> None:
            plan = self.steam_launcher_service.build_open_page(page_type)
            if not plan:
                return
            self.system_facade.open_uri(uri=plan.primary_uri, fallback_url=plan.fallback_url)

        self.action_bus.register(Action.LAUNCH_GAME, _launch_game)
        self.action_bus.register(Action.OPEN_STEAM_PAGE, _open_steam_page)

        self.action_bus.register(Action.TOGGLE_TIMER, self.timer_handler.toggle)
        self.action_bus.register(Action.PAUSE_TIMER, self.timer_handler.pause)
        self.action_bus.register(Action.RESUME_TIMER, self.timer_handler.resume)
        self.action_bus.register(Action.STOP_TIMER, self.timer_handler.stop_and_persist)

        # UI intents via actions
        self.action_bus.register(Action.SAY_HELLO, self.say_hello_facade.say_hello)
        self.action_bus.register(Action.ACTIVATE_PET, lambda **_: self.ui_intents.activate_pet.emit())
        self.action_bus.register(Action.HIDE_PET, lambda **_: self.ui_intents.hide_pet.emit())
        self.action_bus.register(Action.TOGGLE_TOPMOST, lambda **_: self.ui_intents.toggle_topmost.emit())
        self.action_bus.register(Action.OPEN_WINDOW, lambda window_name, **_: self.ui_intents.open_window.emit(window_name))

        # 菜单项 provider 列表（每个 provider 返回 dict 或 None）
        #
        # 注意：provider 在渲染时才会被调用（见 MenuComposer.compose），
        # 因此不要在外层创建/复用 builder 实例并在此处通过闭包引用它们，
        # 否则一旦 builder 引入可变状态（缓存、临时字段等），就可能出现“陈旧菜单状态”。
        # 这里采用“每次调用都新建 builder 并立即 build”的方式，消除隐性共享状态风险。
        action_bus = self.action_bus
        config_manager = self.config_manager
        timer_handler = self.timer_handler
        steam_manager = self.steam_manager
        behavior_manager = self.behavior_manager

        menu_providers = [
            lambda ab=action_bus, cm=config_manager: ExitMenuBuilder(ab, cm).build(),
            lambda ab=action_bus, cm=config_manager: PathMenuBuilder(ab, cm).build(),
            lambda ab=action_bus, cm=config_manager: SteamPageMenuBuilder(ab, cm).build(),
            lambda ab=action_bus, cm=config_manager: ToolMenuBuilder(ab, cm).build_stats_item(),
            lambda ab=action_bus, cm=config_manager, th=timer_handler: TimerMenuBuilder(ab, cm, th).build(),
            lambda ab=action_bus, cm=config_manager, sm=steam_manager: SteamGameMenuBuilder(ab, cm, sm).build_recent_game_item(),
            lambda ab=action_bus, cm=config_manager, sm=steam_manager: SteamGameMenuBuilder(ab, cm, sm).build_quick_launch_item(),
            lambda ab=action_bus, cm=config_manager, bm=behavior_manager: InteractionMenuBuilder(ab, cm, bm).build(),
        ]

        # 菜单布局顺序：由顶层注入，避免耦合在 MenuComposer 中
        menu_layout_keys = [
            "exit",
            "open_path",
            "open_steam_page",
            "stats",
            "timer",
            "launch_recent",
            "launch_favorite",
            "interaction",
        ]

        self.menu_composer = MenuComposer(
            providers=menu_providers,
            layout_keys=menu_layout_keys,
            fill_to=len(menu_layout_keys),
        )
        
        # 初始化窗口工厂
        self.window_factory = WindowFactory(
            self.steam_manager,
            self.config_manager,
            self.timer_handler,
            self.news_manager,
            self.prompt_manager
        )

        # 将新闻抓取错误也汇总到统一错误通道（不影响窗口内错误展示）
        try:
            self.news_manager.on_error.connect(lambda msg: self.ui_intents.error.emit(f"news failed: {msg}"))
        except Exception:
            pass
        
        self.radial_handler = RadialHandler(
            self.menu_composer
        )
        self.window_handler = WindowHandler(
            self.window_factory
        )
        
        # 初始化托盘管理器
        self.tray_handler = TrayHandler(self.action_bus, self.app)
        # 将托盘提醒作为计时提醒通知器
        self.timer_handler.set_notifier(self.tray_handler.show_message)
        # 退出时关闭计时器内部 Qt 定时器
        self.app.aboutToQuit.connect(self.timer_handler.shutdown)

        # 初始化 TimerOverlay (View Helper)
        self.timer_overlay = TimerOverlay(self.timer_handler)

        # 初始化核心组件 (注入依赖)
        self.pet = DesktopPet(
            behavior_manager=self.behavior_manager,
            resource_manager=self.resource_manager,
            timer_overlay=self.timer_overlay
        )
        
        # 注入 BehaviorManager 所需的依赖
        self.behavior_manager.set_dependencies(self.steam_manager, self.llm_service, self.prompt_manager)
        
        # 启动时触发一次推荐
        self.behavior_manager.trigger_startup_behavior()
        
        # 连接计时器状态变化以暂停/恢复 AI 行为
        # 当计时器运行时，我们可能希望 AI 保持专注或安静，或者至少不要随意切换状态
        self.timer_handler.running_state_changed.connect(
            lambda running: self.behavior_manager.set_paused("timer_running", running)
        )

        # 显示宠物
        self.pet.show()
        # 连接信号以同步状态
        self.pet.visibility_changed.connect(self.tray_handler.update_visibility_text)
        self.pet.topmost_changed.connect(self.tray_handler.update_topmost_text)
        
        # 连接宠物交互信号
        self.pet.right_clicked.connect(self.radial_handler.handle_right_click)
        self.pet.double_clicked.connect(lambda: self.action_bus.execute(Action.SAY_HELLO))
        self.radial_handler.menu_hovered_changed.connect(self.pet.on_menu_hover_changed)

        # 气泡 show/hide 会驱动互动上下文变化：若菜单正在显示则即时刷新
        self.behavior_manager.menu_refresh_requested.connect(self.radial_handler.refresh_menu)
        
        # 连接 UI intents（由 ActionBus 触发）
        self.ui_intents.open_window.connect(self.window_handler.open_window)
        self.ui_intents.activate_pet.connect(self.activate_pet)
        self.ui_intents.hide_pet.connect(self.toggle_pet_visibility)
        self.ui_intents.toggle_topmost.connect(self.pet.toggle_topmost)
        self.ui_intents.say_hello.connect(self.on_say_hello)
        self.ui_intents.say_hello_stream_started.connect(self.behavior_manager.request_speech_stream_started)
        self.ui_intents.say_hello_stream_delta.connect(self.behavior_manager.request_speech_stream_delta)
        self.ui_intents.say_hello_stream_done.connect(self.behavior_manager.request_speech_stream_done)
        self.ui_intents.error.connect(self.on_error_occurred)
        self.ui_intents.notification.connect(
            lambda t, m: self.tray_handler.show_message(t, m, QSystemTrayIcon.MessageIcon.Warning, 3000)
        )

        # 启动时异步检查 LLM 可用性
        threading.Thread(target=self._check_llm_startup, daemon=True).start()

    def _check_llm_startup(self):
        """启动时检查 LLM 服务，如果配置了但不可用，则通知用户"""
        # 只有当用户配置了 API Key 时才检查，避免打扰新用户
        if self.config_manager.get("llm_api_key"):
            if not self.llm_service.check_availability():
                self.ui_intents.notification.emit(
                    "LLM 服务不可用", 
                    "无法连接到 LLM 服务，AI 功能已禁用。\n请检查网络或配置。"
                )

    def on_say_hello(self, content):
        """响应打招呼"""
        # 将意图转达给 BehaviorManager，而不是直接操作 UI
        self.behavior_manager.request_speech(content)
        print(f"[Pet Says]: {content}")

    def on_error_occurred(self, error_msg):
        """响应错误信息"""
        print(f"[Error]: {error_msg}")
        self.tray_handler.show_message("错误", error_msg, QSystemTrayIcon.MessageIcon.Warning, 3000)

    def toggle_pet_visibility(self):
        self.pet.set_visibility(not self.pet.isVisible())
    
    def activate_pet(self):
        """
        激活宠物窗口：如果隐藏则显示，然后激活窗口获得焦点
        """
        if not self.pet.isVisible():
            self.pet.show()
        self.pet.activateWindow()
        self.pet.raise_()

    def quit_app(self):
        self.app.quit()
