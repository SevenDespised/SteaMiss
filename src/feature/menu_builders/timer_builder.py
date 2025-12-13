"""
计时器菜单项构建器
"""
from PyQt6.QtWidgets import QApplication
from .base_builder import BaseMenuBuilder
from src.ui.reminder_settings_dialog import ReminderSettingsDialog


class TimerMenuBuilder(BaseMenuBuilder):
    """计时器菜单项构建器"""
    
    def __init__(self, feature_router, config_manager, timer_handler):
        super().__init__(feature_router, config_manager)
        self.timer_handler = timer_handler

    def build(self):
        """根据计时状态构造菜单项"""
        tm = self.timer_handler
        if not tm:
            return {
                'key': 'timer',
                'label': "计时器\n未配置",
                'callback': lambda: None
            }
        
        if tm.is_running():
            # 正在计时：主按钮结束，子按钮暂停/提醒设置
            return {
                'key': 'timer',
                'label': "结束\n计时",
                'callback': lambda: self.feature_router.execute_action("stop_timer"),
                'sub_items': [
                    {
                        'label': "暂停\n计时",
                        'callback': lambda: self.feature_router.execute_action("pause_timer")
                    },
                    self._reminder_sub_item()
                ]
            }
        elif tm.is_paused():
            # 暂停中：主按钮结束，子按钮继续/提醒设置
            return {
                'key': 'timer',
                'label': "结束\n计时",
                'callback': lambda: self.feature_router.execute_action("stop_timer"),
                'sub_items': [
                    {
                        'label': "继续\n计时",
                        'callback': lambda: self.feature_router.execute_action("resume_timer")
                    },
                    self._reminder_sub_item()
                ]
            }
        else:
            # 未计时：主按钮开始 + 提醒设置
            return {
                'key': 'timer',
                'label': "开始\n计时",
                'callback': lambda: self.feature_router.execute_action("toggle_timer"),
                'sub_items': [self._reminder_sub_item()]
            }

    def _reminder_sub_item(self):
        """构造提醒设置子项"""
        return {
            'label': "提醒\n设置",
            'callback': self._open_reminder_dialog
        }

    def _open_reminder_dialog(self):
        """打开提醒设置对话框"""
        if not self.timer_handler:
            return
        # 确保存在应用实例
        app = QApplication.instance()
        parent = app.activeWindow() if app else None
        dialog = ReminderSettingsDialog(self.timer_handler, parent=parent)
        dialog.exec()
