"""
计时器菜单项构建器
"""
from .base_builder import BaseMenuBuilder


class TimerMenuBuilder(BaseMenuBuilder):
    """计时器菜单项构建器"""
    
    def __init__(self, feature_manager, config_manager, timer_manager):
        super().__init__(feature_manager, config_manager)
        self.timer_manager = timer_manager

    def build(self):
        """根据计时状态构造菜单项"""
        tm = self.timer_manager
        if not tm:
            return {
                'key': 'timer',
                'label': "计时器\n未配置",
                'callback': lambda: None
            }
        
        if tm.is_running():
            # 正在计时：主按钮结束，子按钮暂停
            return {
                'key': 'timer',
                'label': "结束\n计时",
                'callback': lambda: self.timer_manager.stop_and_persist(),
                'sub_items': [
                    {
                        'label': "暂停\n计时",
                        'callback': lambda: self.timer_manager.pause()
                    }
                ]
            }
        elif tm.is_paused():
            # 暂停中：主按钮结束，子按钮继续
            return {
                'key': 'timer',
                'label': "结束\n计时",
                'callback': lambda: self.timer_manager.stop_and_persist(),
                'sub_items': [
                    {
                        'label': "继续\n计时",
                        'callback': lambda: self.timer_manager.resume()
                    }
                ]
            }
        else:
            # 未开始：主按钮开始
            return {
                'key': 'timer',
                'label': "开始\n计时",
                'callback': lambda: self.timer_manager.toggle()
            }
