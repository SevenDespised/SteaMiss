"""
计时器显示组件：负责加载背景和数字资源，按给定时间绘制。
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from src.utils.path_utils import resource_path


class TimerDisplay:
    """
    负责计时器的渲染：加载背景和数字资源，按给定时间绘制。
    """

    def __init__(self, digits_dir=None, clock_path=None, target_height=60):
        """
        @param digits_dir: 数字图片目录（默认 assets/digits）
        @param clock_path: 背景图片（默认 assets/clock.png）
        @param target_height: 背景缩放高度，且无背景时作为默认数字高度
        """
        self.digits_dir = digits_dir or resource_path("assets", "digits")
        self.clock_path = clock_path or resource_path("assets", "clock.png")
        self.target_height = target_height

        self.digits_raw = {}
        self.colon_on_raw = None
        self.colon_off_raw = None
        self.clock_bg = None
        self._load_assets()

    def _load_pixmap(self, path):
        if not os.path.exists(path):
            return None
        pix = QPixmap(str(path))
        if pix.isNull():
            return None
        return pix

    def _load_assets(self):
        for i in range(10):
            path = os.path.join(self.digits_dir, f"{i}.png")
            pix = self._load_pixmap(path)
            if pix:
                self.digits_raw[str(i)] = pix

        colon_on_path = os.path.join(self.digits_dir, "colon_on.png")
        colon_off_path = os.path.join(self.digits_dir, "colon_off.png")
        self.colon_on_raw = self._load_pixmap(colon_on_path)
        self.colon_off_raw = self._load_pixmap(colon_off_path)

        if os.path.exists(self.clock_path):
            bg = QPixmap(str(self.clock_path))
            if not bg.isNull():
                self.clock_bg = bg.scaledToHeight(int(self.target_height), Qt.TransformationMode.SmoothTransformation)

    def measure(self, h, m, s, show_on=True):
        """
        计算绘制占用宽高。
        @param h: 小时
        @param m: 分钟
        @param s: 秒
        @param show_on: 是否显示“冒号点亮”
        @return: (width, height)
        """
        _, total_width, max_height = self._get_pixmaps(h, m, s, show_on, with_size=True)
        if self.clock_bg:
            return self.clock_bg.width(), self.clock_bg.height()
        return total_width, max_height

    def draw(self, painter, x, y, h, m, s, show_on=True):
        """
        绘制计时器。
        @param painter: QPainter
        @param x: 左上角 x
        @param y: 左上角 y
        @param h: 小时
        @param m: 分钟
        @param s: 秒
        @param show_on: 是否显示“冒号点亮”
        @return: (width, height)
        """
        pixmaps, total_width, max_height = self._get_pixmaps(h, m, s, show_on, with_size=True)

        draw_x = x
        draw_y = y
        gap = 0

        if self.clock_bg:
            bg_w = self.clock_bg.width()
            bg_h = self.clock_bg.height()
            painter.drawPixmap(draw_x, draw_y, bg_w, bg_h, self.clock_bg)
            # 数字从 x+0.1w, y+0.25h 开始；高度用 0.45h 计算
            draw_x = x + int(bg_w * 0.1)
            draw_y = y + int(bg_h * 0.25)

            # 调整数字间 gap，使整体在背景上居中（占用 0.8w 的可用宽度）
            count = len(pixmaps)
            available = max(bg_w * 0.8 - total_width, 0)
            gap = available / (count - 1) if count > 1 else 0

        for pix in pixmaps:
            painter.drawPixmap(int(draw_x), draw_y + (max_height - pix.height()) // 2, pix.width(), pix.height(), pix)
            draw_x += pix.width() + gap

        if self.clock_bg:
            return self.clock_bg.width(), self.clock_bg.height()
        return total_width, max_height

    def _scale_to_height(self, pix, target_h):
        if not pix:
            return None
        if pix.height() == target_h:
            return pix
        return pix.scaledToHeight(int(target_h), Qt.TransformationMode.SmoothTransformation)

    def _get_pixmaps(self, h, m, s, show_on, with_size=False):
        # 根据背景尺寸决定缩放高度
        base_h = self.target_height
        if self.clock_bg:
            base_h = int(self.clock_bg.height() * 0.45)
        colon_h = int(base_h * 0.5)

        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        pixmaps = []
        for ch in time_str:
            if ch == ":":
                raw = self.colon_on_raw if show_on else self.colon_off_raw
                pix = self._scale_to_height(raw, colon_h)
            else:
                raw = self.digits_raw.get(ch)
                pix = self._scale_to_height(raw, base_h)
            if pix:
                pixmaps.append(pix)

        if not with_size:
            return pixmaps

        total_width = sum(p.width() for p in pixmaps)
        max_height = max((p.height() for p in pixmaps), default=base_h)
        return pixmaps, total_width, max_height


__all__ = ["TimerDisplay"]


