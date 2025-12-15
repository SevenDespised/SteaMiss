import datetime
import json
import math
import os
from PyQt6.QtCore import QTimer
from src.feature_core.timer_support.timer_logic import GameTimer


class TimerHandler:
    """计时器业务层：负责开始/结束、持久化以及状态查询。"""

    DEFAULT_REMINDER_SETTINGS = {
        "timer_end_seconds": None,  # None 表示不自动结束
        "timer_remind_interval_seconds": 0,  # 0 表示不提醒
        "timer_pause_after_remind_seconds": 0  # 0 表示提醒后不暂停
    }

    def __init__(self, log_path=None, config_manager=None, notifier=None):
        self.timer = GameTimer()
        # 默认日志位置
        self.log_path = log_path or os.path.join("config", "timer_log.json")
        self.last_elapsed_seconds = 0.0
        self.config_manager = config_manager
        self.notifier = notifier
        self.reminder_settings = self._load_reminder_settings()
        self.reminder_presets = self._load_presets()

        # 提醒调度状态
        self._next_remind_at = None
        self._auto_paused = False

        # 计时刷新定时器，用于执行结束/提醒逻辑
        self._tick_timer = QTimer()
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._on_tick)
        self._tick_timer.start()

        # 自动恢复定时器
        self._auto_resume_timer = QTimer()
        self._auto_resume_timer.setSingleShot(True)
        self._auto_resume_timer.timeout.connect(self._auto_resume)

    def __del__(self):
        """析构时确保内部定时器停止，避免悬挂任务。"""
        self.shutdown()

    def set_notifier(self, notifier):
        """
        设置提醒回调
        @param notifier: callable(title: str, message: str, icon?, duration?)
        """
        self.notifier = notifier

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
        self._auto_resume_timer.stop()
        self._auto_paused = False
        self.timer.start()
        self._sync_next_reminder()

    def pause(self):
        """暂停计时（不保存）"""
        self._auto_resume_timer.stop()
        self._auto_paused = False
        self.timer.pause()

    def resume(self):
        """恢复计时"""
        self._auto_resume_timer.stop()
        self._auto_paused = False
        self.timer.start()
        self._sync_next_reminder()

    def stop_and_persist(self):
        if not self.is_running() and not self.is_paused():
            return
        self._auto_resume_timer.stop()
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

    def get_overlay_context(self):
        """
        获取用于 UI 覆盖层显示的上下文数据。
        封装了“何时显示”以及“显示什么”的业务逻辑。
        """
        running = self.is_running()
        elapsed = self.get_elapsed_seconds()
        
        # 业务规则：只有在运行中，或者暂停且有累计时间时才显示
        if not running and elapsed <= 0:
            return None
            
        h, m, s = self.get_display_time()
        return {
            "h": h,
            "m": m,
            "s": s,
            "is_running": running
        }

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

    def update_reminder_settings(self, end_seconds, remind_interval_seconds, pause_after_remind_seconds):
        """
        更新提醒配置
        @param end_seconds: None 表示不结束，其余为秒数
        @param remind_interval_seconds: 0 表示不提醒
        @param pause_after_remind_seconds: 0 表示提醒后不暂停
        """
        safe_end = end_seconds if (end_seconds is None or end_seconds > 0) else None
        self.reminder_settings["timer_end_seconds"] = safe_end
        self.reminder_settings["timer_remind_interval_seconds"] = max(0, int(remind_interval_seconds or 0))
        self.reminder_settings["timer_pause_after_remind_seconds"] = max(0, int(pause_after_remind_seconds or 0))
        self._save_reminder_settings()
        self._sync_next_reminder()

    def get_reminder_settings(self):
        """获取当前提醒设置的副本"""
        return dict(self.reminder_settings)

    # 预设管理
    def get_presets(self):
        return list(self.reminder_presets)

    def save_preset(self, name, preset_data):
        if not self.config_manager:
            return
        presets = [p for p in self.reminder_presets if p.get("name") != name]
        presets.append({"name": name, **preset_data})
        self.reminder_presets = presets
        self._save_presets()

    def delete_preset(self, name):
        """按名称删除预设"""
        presets = [p for p in self.reminder_presets if p.get("name") != name]
        if len(presets) == len(self.reminder_presets):
            return
        self.reminder_presets = presets
        self._save_presets()

    def load_preset(self, name):
        for p in self.reminder_presets:
            if p.get("name") == name:
                return dict(p)
        return None

    # --- 内部：提醒与结束调度 ---
    def _load_reminder_settings(self):
        settings = dict(self.DEFAULT_REMINDER_SETTINGS)
        if self.config_manager:
            stored = self.config_manager.get("timer_reminder", {})
            if isinstance(stored, dict):
                settings.update({
                    "timer_end_seconds": stored.get("timer_end_seconds", settings["timer_end_seconds"]),
                    "timer_remind_interval_seconds": stored.get("timer_remind_interval_seconds", settings["timer_remind_interval_seconds"]),
                    "timer_pause_after_remind_seconds": stored.get("timer_pause_after_remind_seconds", settings["timer_pause_after_remind_seconds"])
                })
        return settings

    def _load_presets(self):
        if self.config_manager:
            presets = self.config_manager.get("timer_reminder_presets", [])
            if isinstance(presets, list):
                return presets
        return []

    def _save_reminder_settings(self):
        if not self.config_manager:
            return
        self.config_manager.set("timer_reminder", dict(self.reminder_settings))
        # 同步保存预设列表
        self._save_presets()

    def _sync_next_reminder(self):
        """根据当前累计时间和配置计算下一次提醒时刻"""
        interval = self.reminder_settings.get("timer_remind_interval_seconds", 0)
        if interval <= 0:
            self._next_remind_at = None
            return
        elapsed = self.get_elapsed_seconds()
        # 下一个整区间点
        self._next_remind_at = (math.floor(elapsed / interval) + 1) * interval

    def _on_tick(self):
        """每秒检查结束/提醒条件"""
        running = self.is_running()
        paused = self.is_paused()
        if not running and not paused:
            return

        elapsed = self.get_elapsed_seconds()

        # 仅在计时进行中检查结束时间，避免暂停期误触发
        end_seconds = self.reminder_settings.get("timer_end_seconds")
        if running and end_seconds is not None and elapsed >= end_seconds:
            self.stop_and_persist()
            self._notify("计时结束", "已达到设定的结束时间。")
            return

        # 暂停状态不做提醒，以免重复触发
        if not running:
            return

        # 提醒检测
        interval = self.reminder_settings.get("timer_remind_interval_seconds", 0)
        if interval <= 0:
            return

        if self._next_remind_at is None:
            self._sync_next_reminder()

        if self._next_remind_at is not None and elapsed >= self._next_remind_at:
            self._trigger_reminder(elapsed)

    def _trigger_reminder(self, elapsed):
        """触发提醒并根据配置处理暂停"""
        self._notify("计时提醒", f"已计时 {self.timer.get_formatted_string()}。")

        interval = self.reminder_settings.get("timer_remind_interval_seconds", 0)
        self._next_remind_at = elapsed + interval if interval > 0 else None

        pause_seconds = self.reminder_settings.get("timer_pause_after_remind_seconds", 0)
        if pause_seconds > 0 and self.is_running():
            self._auto_paused = True
            self.timer.pause()
            self._auto_resume_timer.stop()
            self._auto_resume_timer.start(int(pause_seconds * 1000))

    def _auto_resume(self):
        """提醒后的自动恢复"""
        if self._auto_paused and not self.is_running():
            self.timer.start()
        self._auto_paused = False
        self._sync_next_reminder()

    def _notify(self, title, message):
        """统一的提醒触发"""
        if callable(self.notifier):
            try:
                self.notifier(title, message)
                return
            except Exception:
                pass
        # 兜底输出
        print(f"[{title}]: {message}")

    def reset(self):
        self.timer.reset()
        self.last_elapsed_seconds = 0.0
        self._next_remind_at = None
        self._auto_resume_timer.stop()
        self._auto_paused = False

    def shutdown(self):
        """停止内部 Qt 定时器，释放资源。"""
        try:
            if self._tick_timer.isActive():
                self._tick_timer.stop()
        except Exception:
            pass
        try:
            if self._auto_resume_timer.isActive():
                self._auto_resume_timer.stop()
        except Exception:
            pass

    def _save_presets(self):
        if not self.config_manager:
            return
        self.config_manager.set("timer_reminder_presets", list(self.reminder_presets))
