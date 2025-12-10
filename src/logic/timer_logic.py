import time

class GameTimer:
    def __init__(self):
        self.start_time = 0.0
        self.accumulated_time = 0.0
        self.is_running = False
        # 最大时间：99小时 59分 59秒
        self.max_seconds = 99 * 3600 + 59 * 60 + 59

    def start(self):
        """开始或继续计时"""
        if not self.is_running:
            self.start_time = time.time()
            self.is_running = True

    def pause(self):
        """暂停计时"""
        if self.is_running:
            self.accumulated_time += time.time() - self.start_time
            self.is_running = False

    def reset(self):
        """重置计时器"""
        self.accumulated_time = 0.0
        self.is_running = False
        self.start_time = 0.0

    def get_total_seconds(self):
        """获取当前总秒数（浮点数）"""
        total = self.accumulated_time
        if self.is_running:
            total += time.time() - self.start_time
        
        if total > self.max_seconds:
            return float(self.max_seconds)
        return total

    def get_time_parts(self):
        """
        获取时分秒
        :return: (hours, minutes, seconds)
        """
        total_seconds = int(self.get_total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return hours, minutes, seconds

    def get_formatted_string(self):
        """
        获取格式化字符串 HH:MM:SS
        """
        h, m, s = self.get_time_parts()
        return f"{h:02d}:{m:02d}:{s:02d}"
