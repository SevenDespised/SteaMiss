import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QRectF, QRect, QEvent, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QCursor, QRegion

class RadialMenu(QWidget):
    hovered_changed = pyqtSignal(int) # 信号：悬停索引改变 (index, -1表示无悬停)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用 Tool 类型而不是 Popup，以便支持点击穿透 (Popup 会强制抓取鼠标)
        # 配合 changeEvent 里的 ActivationChange 来实现失去焦点自动关闭
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.items = []
        self.hovered_index = -1
        self.hovered_sub_index = -1  # -1 表示未悬停子选项
        self.radius = 180
        self.inner_radius = 120
        self.trigger_radius = 80 # 触发宠物指向动画的半径 (比 inner_radius 小)
        self.just_closed = False # 防止重复触发的标志位
        
        # 设置背景透明圆环宽度，防止鼠标穿透无法正确响应动画
        self.ring_bg_width = self.radius - self.trigger_radius
        
        # 外环配置
        self.outer_ring_thickness = 80
        self.sub_radius = self.radius + self.outer_ring_thickness # 子菜单外径
        self.max_sub_options = 2
        
        self.margin = 30 # 触发区域的额外边距
        
        # 启用鼠标追踪，以便在不按键时也能检测悬停
        self.setMouseTracking(True)

    def set_items(self, items):
        """
        items: list of dict {'label': str, 'callback': callable}
        """
        self.items = items
        # 调整窗口大小以容纳圆盘 (包括子菜单) + 边距
        size = (self.sub_radius + self.margin) * 2
        self.resize(size, size)

    def show_at(self, global_pos):
        """在指定位置显示菜单（居中）"""
        # 计算窗口左上角位置，使圆心对准鼠标
        top_left = global_pos - QPoint(self.width() // 2, self.height() // 2)
        self.move(top_left)
        self.show()
        self.activateWindow() # 确保窗口激活，以便后续能检测到失去焦点
        self.hovered_index = -1
        self.update()

    def changeEvent(self, event):
        """检测窗口激活状态变化，失去焦点时自动关闭"""
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                # 延迟关闭，给 Pet 窗口一点时间来检测状态
                # 但实际上 Pet 的事件处理是在主线程，这里也是主线程
                # 关键问题是：点击穿透后，Pet 接收到点击事件时，Menu 是否已经关闭？
                # 如果 Menu 是 Tool 窗口，点击 Pet 会导致 Menu 失去焦点 -> changeEvent -> close()
                # 然后 Pet 收到 mousePress -> contextMenuEvent
                # 此时 Menu 已经不可见了。
                
                # 我们可以设置一个标志位，表示“刚刚关闭”
                self.just_closed = True
                self.close()
                # 100ms 后重置标志位
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(200, lambda: setattr(self, 'just_closed', False))
                
        super().changeEvent(event)

    def resizeEvent(self, event):
        # 移除 setMask 以解决边缘锯齿问题
        # setMask 会导致硬边缘裁剪，无法抗锯齿
        # cx = self.width() // 2
        # cy = self.height() // 2
        
        # # 外圆区域
        # outer_rect = QRect(cx - self.radius, cy - self.radius, self.radius * 2, self.radius * 2)
        # outer_region = QRegion(outer_rect, QRegion.RegionType.Ellipse)
        
        # # 内圆区域 (挖空)
        # inner_rect = QRect(cx - self.inner_radius, cy - self.inner_radius, self.inner_radius * 2, self.inner_radius * 2)
        # inner_region = QRegion(inner_rect, QRegion.RegionType.Ellipse)
        
        # # 设置遮罩：外圆减去内圆
        # self.setMask(outer_region.subtracted(inner_region))
        
        super().resizeEvent(event)

    def paintEvent(self, event):
        if not self.items:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = QPoint(self.width() // 2, self.height() // 2)
        
        # [关键修复] 绘制一个几乎透明的底圆，用于捕获鼠标事件
        # 解决 Windows 下完全透明区域点击穿透的问题
        # 覆盖整个交互区域 (包括可能的子菜单和边距)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # 计算点击检测区域
        hit_inner = self.trigger_radius - self.margin
        hit_outer = self.sub_radius + self.margin
        hit_thickness = hit_outer - hit_inner
        hit_radius = hit_inner + hit_thickness / 2
        
        # 几乎透明的画笔（Alpha=1）
        pen = QPen(QColor(255, 255, 255, 1), hit_thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        painter.drawEllipse(center, int(hit_radius), int(hit_radius))
        
        count = len(self.items)
        if count == 0: return
        
        angle_step = 360 / count
        
        # 绘制扇形
        for i, item in enumerate(self.items):
            # 计算角度 (Qt 0度是3点钟方向，逆时针旋转)
            start_angle = i * angle_step
            
            path = QPainterPath()
            
            # 1. 移动到内圆起始点
            # QPainterPath.moveTo 接受 QPointF 或 (float, float)
            # QPoint + QPoint 得到 QPoint，但 moveTo 可能需要显式转换或拆分
            p1 = center + QPoint(
                int(self.inner_radius * math.cos(math.radians(start_angle))),
                int(self.inner_radius * math.sin(math.radians(start_angle)))
            )
            path.moveTo(p1.x(), p1.y())
            
            # 2. 连线到外圆起始点
            p2 = center + QPoint(
                int(self.radius * math.cos(math.radians(start_angle))),
                int(self.radius * math.sin(math.radians(start_angle)))
            )
            path.lineTo(p2.x(), p2.y())
            
            # 3. 画外圆弧 (注意 arcTo 参数是矩形和角度)
            rect_outer = QRectF(center.x() - self.radius, center.y() - self.radius, self.radius * 2, self.radius * 2)
            
            current_start = -start_angle
            current_sweep = -angle_step
            
            path = QPainterPath()
            path.arcMoveTo(rect_outer, current_start)
            path.arcTo(rect_outer, current_start, current_sweep)
            
            rect_inner = QRectF(center.x() - self.inner_radius, center.y() - self.inner_radius, self.inner_radius * 2, self.inner_radius * 2)
            # 内圆回连 (反向)
            path.arcTo(rect_inner, current_start + current_sweep, -current_sweep)
            path.closeSubpath()
            
            # 颜色处理
            color = QColor(220, 240, 255, 230) 
            if item is None:
                # 空项：颜色更淡，且不响应悬停高亮
                color = QColor(240, 240, 240, 100)
            elif i == self.hovered_index:
                color = QColor(100, 180, 255, 240) # 高亮色
            
            painter.setBrush(color)
            painter.setPen(QPen(QColor(0, 0, 0, 50), 1))
            painter.drawPath(path)
            
            # 绘制文字
            if item:
                mid_angle = start_angle + angle_step / 2
                text_radius = (self.radius + self.inner_radius) / 2
                
                # 修正：使用正角度计算文字位置
                # 在屏幕坐标系(Y向下)中，math.sin(正角度) 是正值(向下)，对应顺时针旋转
                # 这与我们的扇形绘制逻辑 (0->90 对应 Right->Bottom) 一致
                rad = math.radians(mid_angle) 
                
                text_x = center.x() + text_radius * math.cos(rad)
                text_y = center.y() + text_radius * math.sin(rad)
                
                painter.setPen(QColor(0, 0, 0))
                font = QFont()
                font.setBold(True)
                painter.setFont(font)
                
                # 绘制文字矩形 (增加高度以支持换行)
                text_rect = QRectF(text_x - 40, text_y - 25, 80, 50)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, item['label'])

        # 绘制外环子选项（仅当前悬停的扇区展示）
        if 0 <= self.hovered_index < len(self.items) and self.items[self.hovered_index]:
            sub_items = self.items[self.hovered_index].get('sub_items') or []
            if sub_items:
                angle_step = 360 / count
                start_angle = self.hovered_index * angle_step
                current_start = -start_angle
                current_sweep = -angle_step
                band_height = self.outer_ring_thickness / max(len(sub_items), 1)

                for idx, sub in enumerate(sub_items[:self.max_sub_options]):
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

                    # 绘制子项文字
                    mid_angle = start_angle + angle_step / 2
                    rad = math.radians(mid_angle)
                    text_radius = (r_inner + r_outer) / 2
                    text_x = center.x() + text_radius * math.cos(rad)
                    text_y = center.y() + text_radius * math.sin(rad)
                    text_rect = QRectF(text_x - 40, text_y - 20, 80, 40)
                    painter.setPen(QColor(0, 0, 0))
                    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, sub.get('label', ''))

    def leaveEvent(self, event):
        if self.hovered_index != -1:
            self.hovered_index = -1
            self.hovered_changed.emit(-1)
        self.hovered_sub_index = -1
        self.update()
        super().leaveEvent(event)

    def hideEvent(self, event):
        # 窗口隐藏/关闭时，重置状态
        self.hovered_changed.emit(-1)
        self.hovered_sub_index = -1
        super().hideEvent(event)

    def mouseMoveEvent(self, event):
        center = QPoint(self.width() // 2, self.height() // 2)
        pos = event.pos() - center
        dist = math.sqrt(pos.x()**2 + pos.y()**2)
        
        # 1. 计算角度索引 (通用)
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

        # 2. 计算 UI 高亮索引 (主项位于内环)
        new_hover_index = -1
        new_hover_sub_index = -1
        if self.inner_radius <= dist <= self.radius:
            new_hover_index = angle_index
        elif self.radius < dist <= self.radius + self.outer_ring_thickness and angle_index != -1:
            if self.items[angle_index] and angle_index < len(self.items):
                sub_items = self.items[angle_index].get('sub_items')
            else:
                sub_items = None
            if sub_items:
                new_hover_index = angle_index
                band_height = self.outer_ring_thickness / max(len(sub_items), 1)
                idx = int((dist - self.radius) / band_height)
                new_hover_sub_index = min(idx, len(sub_items) - 1)
        
        # 3. 计算 信号触发索引
        # 逻辑：只有在真正的菜单区域内才触发指向信号
        # 额外区域（margin）仅用于捕获鼠标事件，以便在移出时能正确发送 -1 重置信号
        new_signal_index = -1
        
        # 动态计算有效外半径：如果有子菜单，则延伸到子菜单外径
        has_sub_items = False
        if 0 <= angle_index < len(self.items):
            if self.items[angle_index] and self.items[angle_index].get('sub_items'):
                has_sub_items = True
        
        real_outer = self.sub_radius if has_sub_items else self.radius
        
        # 严格限制在触发半径和有效外半径之间
        if self.trigger_radius <= dist <= real_outer:
            new_signal_index = angle_index

        # 4. 更新 UI 状态
        if new_hover_index != -1 and (new_hover_index >= len(self.items) or self.items[new_hover_index] is None):
            new_hover_index = -1
            new_hover_sub_index = -1

        if self.hovered_index != new_hover_index or self.hovered_sub_index != new_hover_sub_index:
            self.hovered_index = new_hover_index
            self.hovered_sub_index = new_hover_sub_index
            self.update() # 只重绘 UI

        # 5. 发送信号 (使用更宽松的索引)
        # 注意：我们需要记录上一次发送的信号索引，避免重复发送
        if getattr(self, '_last_signal_index', -2) != new_signal_index:
            self._last_signal_index = new_signal_index
            self.hovered_changed.emit(new_signal_index)

    def mousePressEvent(self, event):
        # 右键点击直接关闭菜单
        if event.button() == Qt.MouseButton.RightButton:
            self.close()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # 仅左键释放触发点击
        if event.button() != Qt.MouseButton.LeftButton:
            return
        # 先记录当前选择，再关闭窗口，避免 hideEvent 重置状态导致回调丢失
        callback = None
        if self.hovered_index != -1 and self.items:
            item = self.items[self.hovered_index]
            # 确保 item 不是 None
            if item:
                sub_items = item.get('sub_items') or []
                if 0 <= self.hovered_sub_index < len(sub_items):
                    callback = sub_items[self.hovered_sub_index].get('callback')
                else:
                    callback = item.get('callback')

        # 关闭菜单后再执行回调，确保视觉反馈同时保留所选项
        self.close()
        if callable(callback):
            callback()
