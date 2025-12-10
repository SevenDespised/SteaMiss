import os
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class TimerDisplay:
    """负责计时器的渲染：加载背景和数字资源，按给定时间绘制。"""

    def __init__(self, digits_dir=None, clock_path=None, target_height=26):
        self.digits_dir = digits_dir or os.path.join("assets", "digits")
        self.clock_path = clock_path or os.path.join("assets", "clock.png")
        self.target_height = target_height
        self.digits = {}
        self.colon_on = None
        self.colon_off = None
        self.clock_bg = None
        self._load_assets()

    def _load_scaled_pixmap(self, path):
        if not os.path.exists(path):
            return None
        pix = QPixmap(path)
        if pix.isNull():
            return None
        if pix.height() != self.target_height:
            pix = pix.scaledToHeight(self.target_height, Qt.TransformationMode.SmoothTransformation)
        return pix

    def _load_assets(self):
        for i in range(10):
            path = os.path.join(self.digits_dir, f"{i}.png")
            pix = self._load_scaled_pixmap(path)
            if pix:
                self.digits[str(i)] = pix

        colon_on_path = os.path.join(self.digits_dir, "colon_on.png")
        colon_off_path = os.path.join(self.digits_dir, "colon_off.png")
        self.colon_on = self._load_scaled_pixmap(colon_on_path)
        self.colon_off = self._load_scaled_pixmap(colon_off_path)

        if os.path.exists(self.clock_path):
            bg = QPixmap(self.clock_path)
            if not bg.isNull():
                # 背景高度略大于数字，保证留边
                target_h = int(self.target_height * 1.8)
                bg = bg.scaledToHeight(target_h, Qt.TransformationMode.SmoothTransformation)
                self.clock_bg = bg

    def measure(self, h, m, s, show_on=True):
        """仅计算尺寸，不绘制。"""
        pixmaps = self._get_pixmaps(h, m, s, show_on)
        total_width = sum(p.width() for p in pixmaps)
        max_height = max((p.height() for p in pixmaps), default=self.target_height)
        if self.clock_bg:
            return self.clock_bg.width(), self.clock_bg.height()
        return total_width, max_height

    def draw(self, painter, x, y, h, m, s, show_on=True):
        """
        在 (x, y) 位置绘制计时器。
        show_on: 控制冒号点亮/熄灭（运行中点亮，停止可熄灭）。
        """
        pixmaps = self._get_pixmaps(h, m, s, show_on)

        total_width = sum(p.width() for p in pixmaps)
        max_height = max((p.height() for p in pixmaps), default=self.target_height)

        draw_x = x
        draw_y = y

        # 背景（可选）
        if self.clock_bg:
            bg_w = self.clock_bg.width()
            bg_h = self.clock_bg.height()
            painter.drawPixmap(draw_x, draw_y, bg_w, bg_h, self.clock_bg)
            draw_x += (bg_w - total_width) // 2
            draw_y += (bg_h - max_height) // 2

        for pix in pixmaps:
            painter.drawPixmap(draw_x, draw_y, pix.width(), pix.height(), pix)
            draw_x += pix.width()

        if self.clock_bg:
            return self.clock_bg.width(), self.clock_bg.height()
        return total_width, max_height

    def _get_pixmaps(self, h, m, s, show_on):
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        pixmaps = []
        for ch in time_str:
            if ch == ":":
                pix = self.colon_on if show_on else self.colon_off
            else:
                pix = self.digits.get(ch)
            if pix:
                pixmaps.append(pix)
        return pixmaps
