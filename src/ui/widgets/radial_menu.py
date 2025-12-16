"""
环形菜单组件。
"""

import math

from PyQt6.QtCore import QEvent, QPoint, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget


class RadialMenu(QWidget):
    """
    环形菜单（Tool 窗口，失去焦点自动关闭）。
    """

    hovered_changed = pyqtSignal(int)  # 悬停索引改变（-1 表示无悬停）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.items = []
        self.hovered_index = -1
        self.hovered_sub_index = -1
        self.radius = 180
        self.inner_radius = 120
        self.trigger_radius = 80
        self.just_closed = False

        # 透明区域点击穿透修复用（画一个几乎透明的环）
        self.outer_ring_thickness = 80
        self.sub_radius = self.radius + self.outer_ring_thickness
        self.max_sub_options = 2
        self.margin = 30

        self.setMouseTracking(True)

    def set_items(self, items):
        """
        @param items: list[dict]，元素包含 {'label': str, 'callback': callable, 'sub_items'?: list}
        """
        self.items = items
        size = (self.sub_radius + self.margin) * 2
        self.resize(size, size)

    def show_at(self, global_pos):
        """在指定位置显示菜单（居中）"""
        top_left = global_pos - QPoint(self.width() // 2, self.height() // 2)
        self.move(top_left)
        self.show()
        self.activateWindow()
        self.hovered_index = -1
        self.update()

    def changeEvent(self, event):
        """失去焦点时自动关闭，并设置 just_closed 防抖"""
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.just_closed = True
                self.close()
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(200, lambda: setattr(self, "just_closed", False))
        super().changeEvent(event)

    def paintEvent(self, event):
        if not self.items:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = QPoint(self.width() // 2, self.height() // 2)

        # 画一个几乎透明的环，捕获鼠标事件（Windows 透明穿透）
        hit_inner = self.trigger_radius - self.margin
        hit_outer = self.sub_radius + self.margin
        hit_thickness = hit_outer - hit_inner
        hit_radius = hit_inner + hit_thickness / 2

        pen = QPen(QColor(255, 255, 255, 1), hit_thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, int(hit_radius), int(hit_radius))

        count = len(self.items)
        if count == 0:
            return

        angle_step = 360 / count

        # 主扇区
        for i, item in enumerate(self.items):
            start_angle = i * angle_step

            rect_outer = QRectF(center.x() - self.radius, center.y() - self.radius, self.radius * 2, self.radius * 2)
            rect_inner = QRectF(
                center.x() - self.inner_radius, center.y() - self.inner_radius, self.inner_radius * 2, self.inner_radius * 2
            )

            current_start = -start_angle
            current_sweep = -angle_step

            path = QPainterPath()
            path.arcMoveTo(rect_outer, current_start)
            path.arcTo(rect_outer, current_start, current_sweep)
            path.arcTo(rect_inner, current_start + current_sweep, -current_sweep)
            path.closeSubpath()

            color = QColor(220, 240, 255, 230)
            if item is None:
                color = QColor(240, 240, 240, 100)
            elif i == self.hovered_index:
                color = QColor(100, 180, 255, 240)

            painter.setBrush(color)
            painter.setPen(QPen(QColor(0, 0, 0, 50), 1))
            painter.drawPath(path)

            if item:
                mid_angle = start_angle + angle_step / 2
                text_radius = (self.radius + self.inner_radius) / 2
                rad = math.radians(mid_angle)
                text_x = center.x() + text_radius * math.cos(rad)
                text_y = center.y() + text_radius * math.sin(rad)

                painter.setPen(QColor(0, 0, 0))
                font = QFont()
                font.setBold(True)
                painter.setFont(font)

                text_rect = QRectF(text_x - 40, text_y - 25, 80, 50)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, item["label"])

        # 子菜单外环（仅当前悬停展示）
        if 0 <= self.hovered_index < len(self.items) and self.items[self.hovered_index]:
            sub_items = self.items[self.hovered_index].get("sub_items") or []
            if sub_items:
                start_angle = self.hovered_index * angle_step
                current_start = -start_angle
                current_sweep = -angle_step
                band_height = self.outer_ring_thickness / max(len(sub_items), 1)

                for idx, sub in enumerate(sub_items[: self.max_sub_options]):
                    r_inner = self.radius + idx * band_height
                    r_outer = self.radius + (idx + 1) * band_height
                    rect_outer = QRectF(center.x() - r_outer, center.y() - r_outer, r_outer * 2, r_outer * 2)
                    rect_inner = QRectF(center.x() - r_inner, center.y() - r_inner, r_inner * 2, r_inner * 2)

                    path = QPainterPath()
                    path.arcMoveTo(rect_outer, current_start)
                    path.arcTo(rect_outer, current_start, current_sweep)
                    path.arcTo(rect_inner, current_start + current_sweep, -current_sweep)
                    path.closeSubpath()

                    color = QColor(220, 240, 255, 210)
                    if idx == self.hovered_sub_index:
                        color = QColor(120, 200, 255, 240)
                    painter.setBrush(color)
                    painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
                    painter.drawPath(path)

                    mid_angle = start_angle + angle_step / 2
                    rad = math.radians(mid_angle)
                    text_radius = (r_inner + r_outer) / 2
                    text_x = center.x() + text_radius * math.cos(rad)
                    text_y = center.y() + text_radius * math.sin(rad)
                    text_rect = QRectF(text_x - 40, text_y - 20, 80, 40)
                    painter.setPen(QColor(0, 0, 0))
                    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, sub.get("label", ""))

    def leaveEvent(self, event):
        if self.hovered_index != -1:
            self.hovered_index = -1
            self.hovered_changed.emit(-1)
        self.hovered_sub_index = -1
        self.update()
        super().leaveEvent(event)

    def hideEvent(self, event):
        self.hovered_changed.emit(-1)
        self.hovered_sub_index = -1
        super().hideEvent(event)

    def mouseMoveEvent(self, event):
        center = QPoint(self.width() // 2, self.height() // 2)
        pos = event.pos() - center
        dist = math.sqrt(pos.x() ** 2 + pos.y() ** 2)

        angle_index = -1
        count = len(self.items)
        if count > 0:
            mouse_angle = math.degrees(math.atan2(pos.y(), pos.x()))
            if mouse_angle < 0:
                mouse_angle += 360
            step = 360 / count
            idx = int(mouse_angle / step)
            if 0 <= idx < count:
                angle_index = idx

        new_hover_index = -1
        new_hover_sub_index = -1
        if self.inner_radius <= dist <= self.radius:
            new_hover_index = angle_index
        elif self.radius < dist <= self.radius + self.outer_ring_thickness and angle_index != -1:
            sub_items = None
            if 0 <= angle_index < len(self.items) and self.items[angle_index]:
                sub_items = self.items[angle_index].get("sub_items")
            if sub_items:
                new_hover_index = angle_index
                band_height = self.outer_ring_thickness / max(len(sub_items), 1)
                idx = int((dist - self.radius) / band_height)
                new_hover_sub_index = min(idx, len(sub_items) - 1)

        # 信号触发索引：只在真实菜单区域内触发
        new_signal_index = -1
        has_sub_items = False
        if 0 <= angle_index < len(self.items):
            if self.items[angle_index] and self.items[angle_index].get("sub_items"):
                has_sub_items = True
        real_outer = self.sub_radius if has_sub_items else self.radius
        if self.trigger_radius <= dist <= real_outer:
            new_signal_index = angle_index

        if new_hover_index != -1 and (new_hover_index >= len(self.items) or self.items[new_hover_index] is None):
            new_hover_index = -1
            new_hover_sub_index = -1

        if self.hovered_index != new_hover_index or self.hovered_sub_index != new_hover_sub_index:
            self.hovered_index = new_hover_index
            self.hovered_sub_index = new_hover_sub_index
            self.update()

        if getattr(self, "_last_signal_index", -2) != new_signal_index:
            self._last_signal_index = new_signal_index
            self.hovered_changed.emit(new_signal_index)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.close()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        callback = None
        if self.hovered_index != -1 and self.items:
            item = self.items[self.hovered_index]
            if item:
                sub_items = item.get("sub_items") or []
                if 0 <= self.hovered_sub_index < len(sub_items):
                    callback = sub_items[self.hovered_sub_index].get("callback")
                else:
                    callback = item.get("callback")

        self.close()
        if callable(callback):
            callback()


__all__ = ["RadialMenu"]


