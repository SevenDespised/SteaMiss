import typing
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QPainter
from src.feature.handlers.timer_handler import TimerHandler
from src.ui.timer_display import TimerDisplay


class TimerOverlay:
    """负责在给定区域内绘制计时器，解耦宠物窗口与计时器绘制细节。"""

    def __init__(self, timer_handler: TimerHandler, display: TimerDisplay | None = None, margin: int = 5):
        self.timer_handler = timer_handler
        self.display = display or TimerDisplay()
        self.margin = margin

    def draw(self, painter: QPainter, container: QRect) -> None:
        if not self.timer_handler or not self.display:
            return

        # 获取渲染上下文，不关心具体的显示条件逻辑
        ctx = self.timer_handler.get_overlay_context()
        if not ctx:
            return
        h, m, s, running= ctx['h'], ctx['m'], ctx['s'], ctx['is_running']
        w_draw, h_draw = self.display.measure(h, m, s, show_on=running)

        x = container.x() + (container.width() - w_draw) // 2
        y = container.y() + container.height() - h_draw - self.margin

        self.display.draw(painter, x, y, h, m, s, show_on=running)
