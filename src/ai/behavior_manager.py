import time
from PyQt6.QtCore import QObject, pyqtSignal
from src.ai.states import (
    StateType, 
    SpeakingSubStateType, 
    AIState, 
    AISubState, 
    IdleState, 
    SpeakingState, 
    GameRecommendationSubState,
    NewsPushSubState,
    FreeGamePushSubState,
    DiscountPushSubState,
)

# --- BehaviorManager ---

class BehaviorManager(QObject):
    # 定义信号：请求说话
    speech_requested = pyqtSignal(str)
    # 流式说话：开始/增量/结束
    speech_stream_started = pyqtSignal(str)  # request_id
    speech_stream_delta = pyqtSignal(str, str)  # request_id, delta
    speech_stream_done = pyqtSignal(str)  # request_id
    # 定义信号：请求刷新菜单（例如状态变化影响互动项）
    menu_refresh_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._states: dict[StateType, AIState] = {}
        self._speaking_sub_states: dict[SpeakingSubStateType, AISubState] = {}
        
        self._current_state_type: StateType = StateType.IDLE
        self._current_state: AIState = None
        
        self._pause_reasons = set()
        
        # Dependencies
        self.steam_manager = None
        self.llm_service = None
        self.prompt_manager = None
        
        # State Data
        self.last_recommend_time = time.time()
        self.current_recommended_game = None

        # UI interaction context (driven by speech bubble lifecycle)
        self.interaction_context = None
        self._pending_interaction_context = None

        # Register default states
        self.register_state(StateType.IDLE, IdleState())
        self.register_state(StateType.SPEAKING, SpeakingState())
        
        self.register_speaking_sub_state(SpeakingSubStateType.GAME_RECOMMENDATION, GameRecommendationSubState())
        self.register_speaking_sub_state(SpeakingSubStateType.NEWS_PUSH, NewsPushSubState())
        self.register_speaking_sub_state(SpeakingSubStateType.FREE_GAME_PUSH, FreeGamePushSubState())
        self.register_speaking_sub_state(SpeakingSubStateType.DISCOUNT_PUSH, DiscountPushSubState())
        
        # Initialize
        self._current_state = self._states[self._current_state_type]
        self._current_state.enter(self)

    def set_dependencies(self, steam_manager, llm_service, prompt_manager=None):
        self.steam_manager = steam_manager
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def set_paused(self, reason: str, paused: bool):
        """
        设置暂停状态。
        如果存在任何暂停原因，状态机将停止更新。
        """
        if paused:
            self._pause_reasons.add(reason)
            # 暂停时强制切回 IDLE 状态
            self.transition_to(StateType.IDLE)
        else:
            self._pause_reasons.discard(reason)

    def is_paused(self) -> bool:
        return len(self._pause_reasons) > 0

    def register_state(self, state_type: StateType, state: AIState):
        """开放接口：注册新的主状态"""
        self._states[state_type] = state

    def register_speaking_sub_state(self, sub_state_type: SpeakingSubStateType, sub_state: AISubState):
        """开放接口：注册新的说话子状态"""
        self._speaking_sub_states[sub_state_type] = sub_state

    def get_speaking_sub_state(self, sub_state_type: SpeakingSubStateType) -> AISubState:
        return self._speaking_sub_states.get(sub_state_type)

    def transition_to(self, state_type: StateType):
        if state_type not in self._states:
            return
            
        if self._current_state:
            self._current_state.exit(self)
            
        self._current_state_type = state_type
        self._current_state = self._states[state_type]
        self._current_state.enter(self)

    def request_speech(self, content: str, interaction_context=None):
        """外部请求 AI 说话（显示气泡）。

        交互上下文同步策略：
        - 以气泡显示为起点：在气泡 show 时消费 pending context 并应用到菜单；
        - 以气泡隐藏为终点：在气泡 hide 时清空上下文并刷新菜单。

        @param interaction_context: 可选，供“互动”菜单渲染的上下文信息。
        """
        self._pending_interaction_context = interaction_context
        self.speech_requested.emit(content)

    def request_speech_stream_started(self, request_id: str, interaction_context=None) -> None:
        """开始一次流式说话。

        注意：上下文同步仍以“气泡 show”为起点，因此这里也复用 pending ctx。
        """
        self._pending_interaction_context = interaction_context
        self.speech_stream_started.emit(request_id)

    def request_speech_stream_delta(self, request_id: str, delta: str) -> None:
        """追加一段流式文本（delta）。"""
        self.speech_stream_delta.emit(request_id, delta)

    def request_speech_stream_done(self, request_id: str) -> None:
        """结束一次流式说话。"""
        self.speech_stream_done.emit(request_id)

    def request_menu_refresh(self) -> None:
        """请求 UI 刷新一次环形菜单（若正在显示则更新内容）。"""
        self.menu_refresh_requested.emit()

    def consume_pending_interaction_context(self):
        """由 UI 在气泡显示时调用：取出本次说话携带的上下文。"""
        ctx = self._pending_interaction_context
        self._pending_interaction_context = None
        return ctx

    def set_interaction_context(self, ctx) -> None:
        """设置当前互动上下文并刷新菜单。"""
        self.interaction_context = ctx
        self.request_menu_refresh()

    def clear_interaction_context(self) -> None:
        """清空当前互动上下文并刷新菜单。"""
        self.interaction_context = None
        self.current_recommended_game = None
        self._pending_interaction_context = None
        self.request_menu_refresh()

    def update(self, is_dragging):
        """
        每帧调用，返回当前应该处于的状态名称（用于动画）
        """
        if is_dragging:
            return "dragged"
            
        if self.is_paused():
            return "idle"

        if self._current_state:
            return self._current_state.update(self)
            
        return "idle"

    def get_next_frame(self, state, current_frame_index):
        """
        根据状态计算下一帧图片的索引
        """
        return current_frame_index + 1

    def trigger_startup_behavior(self):
        """
        Trigger behavior on startup (e.g. game recommendation).
        """
        self.transition_to(StateType.SPEAKING)
