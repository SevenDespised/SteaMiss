import random
from PyQt6.QtCore import QObject, pyqtSignal

class BehaviorManager(QObject):
    # 定义信号：请求说话
    speech_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_state = "idle"
        self.state_timer = 0
        
    def request_speech(self, content):
        """
        外部请求 AI 说话（例如响应用户交互）
        """
        # 这里可以加入逻辑：比如正在睡觉时被打扰会生气
        self.speech_requested.emit(content)
        # 同时可以切换状态，例如切换到 "happy" 或 "talking"
        # self.current_state = "happy" 

    def update(self, is_dragging):
        """
        每帧调用，返回当前应该处于的状态
        """
        # 1. 优先级最高的交互状态
        if is_dragging:
            self.current_state = "dragged"
            return self.current_state

        # 2. 如果从交互状态恢复
        if self.current_state == "dragged":
            self.current_state = "idle"
            
        # 3. 简单的随机行为逻辑 (示例)
        # 可以在这里扩展更复杂的 AI，比如饥饿度、心情值等
        self.state_timer += 1
        if self.state_timer > 100: # 每隔一段时间尝试改变状态
            self.state_timer = 0
            
            # [新功能] 调用 AI 决策接口
            ai_decision = self.decide_ai_behavior()
            if ai_decision:
                # TODO: 根据决策执行具体逻辑
                # self.current_state = ai_decision['state']
                pass

            if random.random() > 0.7:
                self.current_state = "walk" if self.current_state == "idle" else "idle"
                # print(f"AI 决定切换状态到: {self.current_state}")
        
        return self.current_state

    def decide_ai_behavior(self):
        """
        [接口] 根据随机数决定 AI 的各种行为
        
        这个接口负责生成随机数，并根据概率分布决定 AI 接下来要做什么。
        目前仅开放接口，不实现具体行为。
        
        Returns:
            dict or None: 包含行为类型和参数的字典，例如:
                          {'type': 'say', 'content': '你好'}
                          {'type': 'move', 'target': (100, 100)}
                          {'type': 'emote', 'name': 'happy'}
        """
        # 1. 生成随机数 (0.0 - 1.0)
        roll = random.random()
        
        # 2. 行为判定逻辑 (预留)
        # 示例结构：
        # if roll < 0.01:
        #     return {'type': 'special_event', 'id': 1}
        # elif roll < 0.05:
        #     return {'type': 'emote', 'name': 'blink'}
            
        return None

    def get_next_frame(self, state, current_frame_index):
        """
        根据状态计算下一帧图片的索引
        """
        # 这里未来可以对接更复杂的动画系统
        return current_frame_index + 1
