"""
计时器覆盖层：在给定区域内绘制计时器，解耦宠物窗口与计时器绘制细节。
"""

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QPainter

from src.feature_core.handlers.timer_handler import TimerHandler
from src.ui.widgets.timer_display import TimerDisplay


class TimerOverlay:
    """
    负责在给定区域内绘制计时器，解耦宠物窗口与计时器绘制细节。
    """

    def __init__(self, timer_handler: TimerHandler, display: TimerDisplay | None = None, margin: int = 5):
        """
        @param timer_handler: TimerHandler（提供 overlay context）
        @param display: TimerDisplay（渲染资源与绘制）
        @param margin: 距离容器底部的边距
        """
        self.timer_handler = timer_handler
        self.display = display or TimerDisplay()
        self.margin = margin

    def draw(self, painter: QPainter, container: QRect) -> None:
        """
        绘制覆盖层。
        @param painter: QPainter
        @param container: 容器区域（通常是 DesktopPet 的 rect）
        """
        if not self.timer_handler or not self.display:
            return

        ctx = self.timer_handler.get_overlay_context()
        if not ctx:
            return

        h, m, s, running = ctx["h"], ctx["m"], ctx["s"], ctx["is_running"]
        w_draw, h_draw = self.display.measure(h, m, s, show_on=running)

        x = container.x() + (container.width() - w_draw) // 2
        y = container.y() + container.height() - h_draw - self.margin
        self.display.draw(painter, x, y, h, m, s, show_on=running)


__all__ = ["TimerOverlay"]


