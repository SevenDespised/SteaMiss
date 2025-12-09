import random

class BehaviorManager:
    def __init__(self):
        self.current_state = "idle"
        self.state_timer = 0
        
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
            if random.random() > 0.7:
                self.current_state = "walk" if self.current_state == "idle" else "idle"
                # print(f"AI 决定切换状态到: {self.current_state}")
        
        return self.current_state

    def get_next_frame(self, state, current_frame_index):
        """
        根据状态计算下一帧图片的索引
        """
        # 这里未来可以对接更复杂的动画系统
        return current_frame_index + 1
