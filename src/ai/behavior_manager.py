import time
from PyQt6.QtCore import QObject, pyqtSignal
from src.ai.states import (
    StateType, 
    SpeakingSubStateType, 
    AIState, 
    AISubState, 
    IdleState, 
    SpeakingState, 
    GameRecommendationSubState
)

# --- BehaviorManager ---

class BehaviorManager(QObject):
    # 定义信号：请求说话
    speech_requested = pyqtSignal(str)

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

        # Register default states
        self.register_state(StateType.IDLE, IdleState())
        self.register_state(StateType.SPEAKING, SpeakingState())
        
        self.register_speaking_sub_state(SpeakingSubStateType.GAME_RECOMMENDATION, GameRecommendationSubState())
        
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

    def request_speech(self, content):
        """
        外部请求 AI 说话（例如响应用户交互）
        """
        self.speech_requested.emit(content)

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
