import json
import os
import datetime
from src.logic.timer_logic import GameTimer


class TimerManager:
    """计时器业务层：负责开始/结束、持久化以及状态查询。"""

    def __init__(self, log_path=None):
        self.timer = GameTimer()
        # 默认日志位置
        self.log_path = log_path or os.path.join("config", "timer_log.json")
        self.last_elapsed_seconds = 0.0

    def is_running(self):
        return self.timer.is_running

    def is_paused(self):
        # 既不是 running，又有 accumulated_time，说明是暂停状态
        return not self.timer.is_running and self.timer.accumulated_time > 0

    def toggle(self):
        """开始/结束计时，返回当前是否正在计时。"""
        if self.is_running():
            self.stop_and_persist()
            return False
        self.start()
        return True

    def start(self):
        self.timer.start()

    def pause(self):
        """暂停计时（不保存）"""
        self.timer.pause()

    def resume(self):
        """恢复计时"""
        self.timer.start()

    def stop_and_persist(self):
        if not self.is_running() and not self.is_paused():
            return
        self.timer.pause()
        self.last_elapsed_seconds = self.timer.get_total_seconds()
        self._persist_record()
        # 只有在真正结束并保存后才重置，清除时钟图像
        self.reset()

    def get_elapsed_seconds(self):
        # 返回当前累计秒数（运行中则包含实时）
        return self.timer.get_total_seconds()

    def get_display_time(self):
        # 返回 (h, m, s)
        return self.timer.get_time_parts()

    def reset(self):
        self.timer.reset()
        self.last_elapsed_seconds = 0.0

    def _persist_record(self):
        """将结束时间与耗时写入 json，追加模式。"""
        record = {
            "end_at": datetime.datetime.now().isoformat(),
            "elapsed_seconds": int(self.last_elapsed_seconds),
            "elapsed_hms": self.timer.get_formatted_string()
        }

        data = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
            except Exception:
                data = []

        data.append(record)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
