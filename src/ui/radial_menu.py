import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QRectF, QRect, QEvent
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QCursor, QRegion

class RadialMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用 Tool 类型而不是 Popup，以便支持点击穿透 (Popup 会强制抓取鼠标)
        # 配合 changeEvent 里的 ActivationChange 来实现失去焦点自动关闭
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.items = []
        self.hovered_index = -1
        self.radius = 180
        self.inner_radius = 120
        
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
        self.activateWindow() # 确保窗口激活，以便后续能检测到失去焦点
        self.hovered_index = -1
        self.update()

    def changeEvent(self, event):
        """检测窗口激活状态变化，失去焦点时自动关闭"""
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.close()
        super().changeEvent(event)

    def resizeEvent(self, event):
        cx = self.width() // 2
        cy = self.height() // 2
        
        # 外圆区域
        outer_rect = QRect(cx - self.radius, cy - self.radius, self.radius * 2, self.radius * 2)
        outer_region = QRegion(outer_rect, QRegion.RegionType.Ellipse)
        
        # 内圆区域 (挖空)
        inner_rect = QRect(cx - self.inner_radius, cy - self.inner_radius, self.inner_radius * 2, self.inner_radius * 2)
        inner_region = QRegion(inner_rect, QRegion.RegionType.Ellipse)
        
        # 设置遮罩：外圆减去内圆
        self.setMask(outer_region.subtracted(inner_region))
        
        super().resizeEvent(event)

    def paintEvent(self, event):
        if not self.items:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = QPoint(self.width() // 2, self.height() // 2)
        count = len(self.items)
        if count == 0: return
        
        angle_step = 360 / count
        
        # 计算起始角度偏移，使菜单关于垂直轴对称
        # 默认0度在3点钟方向。我们希望第一个扇区(index 0)位于正上方(270度)
        # 并且扇区中心对准270度。
        # 扇区范围是 angle_step。所以起始边应在 270 - angle_step/2
        rotation_offset = 270 - angle_step / 2
        
        # 绘制扇形
        for i, item in enumerate(self.items):
            # 计算角度 (Qt 0度是3点钟方向，逆时针旋转)
            # 加上偏移量
            start_angle = i * angle_step + rotation_offset
            
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
            
            # Qt 的 arcTo 使用的是 (startAngle, sweepLength)
            # 这里的角度是逆时针为正，0度在3点钟
            # 我们计算出的 start_angle 是数学角度（也是逆时针，0度在3点钟）
            # 但是 QPainterPath.arcTo 的角度参数也是一样的定义
            # 唯一要注意的是，我们之前的代码用了 -start_angle，可能是为了顺时针排列？
            # 让我们统一使用顺时针排列 item，即 index 0 在 12点，index 1 在 1点...
            # 顺时针意味着角度减小。
            # 所以 item i 的中心角度应该是 270 - i * angle_step
            # 起始角度应该是 270 - i * angle_step + angle_step/2
            # 结束角度应该是 270 - i * angle_step - angle_step/2
            # 让我们重新定义逻辑：
            
            # 采用顺时针布局
            # Item 0 中心: 270度
            # Item 0 范围: [270 + step/2, 270 - step/2]
            # Item i 中心: 270 - i * step
            # Item i 起始(逆时针方向的边缘): 270 - i * step + step/2
            # Item i 结束(逆时针方向的边缘): 270 - i * step - step/2
            # Sweep: -step (顺时针扫过)
            
            item_center_angle = 270 - i * angle_step
            arc_start_angle = item_center_angle + angle_step / 2
            arc_sweep_angle = -angle_step
            
            # 重新计算 p1, p2 基于 arc_start_angle
            p1 = center + QPoint(
                int(self.inner_radius * math.cos(math.radians(arc_start_angle))),
                int(self.inner_radius * math.sin(math.radians(arc_start_angle)))
            )
            
            p2 = center + QPoint(
                int(self.radius * math.cos(math.radians(arc_start_angle))),
                int(self.radius * math.sin(math.radians(arc_start_angle)))
            )
            
            path = QPainterPath()
            path.moveTo(p1)
            path.lineTo(p2)
            
            path.arcTo(rect_outer, arc_start_angle, arc_sweep_angle)
            
            rect_inner = QRectF(center.x() - self.inner_radius, center.y() - self.inner_radius, self.inner_radius * 2, self.inner_radius * 2)
            # 内圆回连 (反向扫过，即 +angle_step，但因为是回连，是从结束点画到起始点)
            # arcTo 会自动连线到圆弧起点
            # 我们现在的点在 外圆结束点。
            # 我们需要画内圆弧，从 结束角度 到 起始角度。
            # 内圆弧起始角度: arc_start_angle + arc_sweep_angle (即结束角度)
            # 内圆弧扫过角度: -arc_sweep_angle (即 +angle_step)
            path.arcTo(rect_inner, arc_start_angle + arc_sweep_angle, -arc_sweep_angle)
            
            path.closeSubpath()
            
            # 颜色处理
            color = QColor(255, 255, 255, 220)
            if i == self.hovered_index:
                color = QColor(100, 180, 255, 240) # 高亮色
            
            painter.setBrush(color)
            painter.setPen(QPen(QColor(0, 0, 0, 50), 1))
            painter.drawPath(path)
            
            # 绘制文字
            # 文字位置在扇形中心
            text_radius = (self.radius + self.inner_radius) / 2
            rad = math.radians(item_center_angle) 
            
            text_x = center.x() + text_radius * math.cos(rad)
            text_y = center.y() + text_radius * math.sin(rad) # Y轴向下，sin正值向下，符合逻辑
            
            painter.setPen(QColor(0, 0, 0))
            font = QFont()
            font.setBold(True)
            painter.setFont(font)
            
            # 绘制文字矩形 (增加高度以支持换行)
            text_rect = QRectF(text_x - 40, text_y - 25, 80, 50)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, item['label'])

    def leaveEvent(self, event):
        self.hovered_index = -1
        self.update()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        center = QPoint(self.width() // 2, self.height() // 2)
        pos = event.pos() - center
        dist = math.sqrt(pos.x()**2 + pos.y()**2)
        
        if dist < self.inner_radius or dist > self.radius:
            self.hovered_index = -1
        else:
            # 计算角度 (0-360, 0在3点钟, 逆时针增加)
            angle = math.degrees(math.atan2(pos.y(), pos.x()))
            if angle < 0:
                angle += 360
            
            # 映射回 index
            # 我们使用的逻辑是: Item i Center = 270 - i * step
            # Item i Range = [270 - i*step - step/2, 270 - i*step + step/2]
            # 注意角度循环 0-360
            
            # 为了简化计算，我们将鼠标角度和 Item 0 中心对齐
            # Item 0 中心是 270。
            # 相对角度 = 270 - angle
            # 这样 Item 0 就在 0 度附近。
            # index = round(relative_angle / step)
            
            # 处理 270 - angle 的周期性
            # 例如 angle = 275 (Item 0 范围内), 270 - 275 = -5
            # angle = 265 (Item 0 范围内), 270 - 265 = 5
            # angle = 0 (3点钟), 270 - 0 = 270.
            
            count = len(self.items)
            if count > 0:
                step = 360 / count
                
                # 将角度转换到以 270 为起点的顺时针坐标系
                # 270 -> 0
                # 260 -> 10
                # 280 -> -10 (350)
                
                # 公式: (270 - angle + 360 + step/2) % 360
                # 加上 step/2 是为了让 index 从 0 开始而不是从 -0.5 开始
                # 比如 Item 0 范围是 [-step/2, step/2]
                # 加上 step/2 后范围是 [0, step] -> int(...) -> 0
                
                relative_angle = (270 - angle + 360 + step / 2) % 360
                index = int(relative_angle / step)
                
                if 0 <= index < count:
                    self.hovered_index = index
                else:
                    self.hovered_index = -1 # Should not happen if math is right
        
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
        # 1. 先关闭菜单 (符合用户直觉，点击即消失)
        self.close()
        if self.hovered_index != -1 and self.items:
            item = self.items[self.hovered_index]
            # 2. 再执行回调
            if 'callback' in item:
                item['callback']()
        else:
            pass
