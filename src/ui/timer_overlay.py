import typing
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QPainter
from src.feature.timer_manager import TimerManager
from src.ui.timer_display import TimerDisplay


class TimerOverlay:
    """负责在给定区域内绘制计时器，解耦宠物窗口与计时器绘制细节。"""

    def __init__(self, timer_manager: TimerManager | None, display: TimerDisplay | None = None, margin: int = 5):
        self.timer_manager = timer_manager
        self.display = display or TimerDisplay()
        self.margin = margin

    def draw(self, painter: QPainter, container: QRect) -> None:
        if not self.timer_manager or not self.display:
            return

        tm = self.timer_manager
        elapsed = tm.get_elapsed_seconds()
        running = tm.is_running()
        if not running and elapsed <= 0:
            return

        h, m, s = tm.get_display_time()
        w_draw, h_draw = self.display.measure(h, m, s, show_on=running)

        x = container.x() + (container.width() - w_draw) // 2
        y = container.y() + container.height() - h_draw - self.margin

        self.display.draw(painter, x, y, h, m, s, show_on=running)
