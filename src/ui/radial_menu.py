import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QCursor

class RadialMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Popup 属性会让窗口在点击外部时自动关闭
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.items = []
        self.hovered_index = -1
        self.radius = 100
        self.inner_radius = 30 
        
        # 启用鼠标追踪，以便在不按键时也能检测悬停
        self.setMouseTracking(True)

    def set_items(self, items):
        """
        items: list of dict {'label': str, 'callback': callable}
        """
        self.items = items
        # 调整窗口大小以容纳圆盘
        size = self.radius * 2 + 20
        self.resize(size, size)

    def show_at(self, global_pos):
        """在指定位置显示菜单（居中）"""
        # 计算窗口左上角位置，使圆心对准鼠标
        top_left = global_pos - QPoint(self.width() // 2, self.height() // 2)
        self.move(top_left)
        self.show()
        self.hovered_index = -1
        self.update()

    def paintEvent(self, event):
        if not self.items:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = QPoint(self.width() // 2, self.height() // 2)
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
            color = QColor(255, 255, 255, 220)
            if i == self.hovered_index:
                color = QColor(100, 180, 255, 240) # 高亮色
            
            painter.setBrush(color)
            painter.setPen(QPen(QColor(0, 0, 0, 50), 1))
            painter.drawPath(path)
            
            # 绘制文字
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

    def mouseMoveEvent(self, event):
        center = QPoint(self.width() // 2, self.height() // 2)
        pos = event.pos() - center
        dist = math.sqrt(pos.x()**2 + pos.y()**2)
        
        if dist < self.inner_radius or dist > self.radius:
            self.hovered_index = -1
        else:
            # 计算角度
            angle = math.degrees(math.atan2(pos.y(), pos.x()))
            if angle < 0:
                angle += 360
            
            mouse_angle = math.degrees(math.atan2(pos.y(), pos.x()))
            if mouse_angle < 0:
                mouse_angle += 360
            count = len(self.items)
            if count > 0:
                step = 360 / count
                index = int(mouse_angle / step)
                if 0 <= index < count:
                    self.hovered_index = index
        
        self.update()

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

        if self.hovered_index != -1 and self.items:
            item = self.items[self.hovered_index]
            
            # 1. 先关闭菜单 (符合用户直觉，点击即消失)
            self.close()
            
            # 2. 再执行回调
            if 'callback' in item:
                item['callback']()
        else:
            # 如果点击的是中心区域 (hovered_index == -1)
            # 我们选择不关闭菜单，防止用户只是松开右键时意外关闭
            # 用户可以通过点击菜单外部来关闭它 (Popup 属性会自动处理)
            pass
