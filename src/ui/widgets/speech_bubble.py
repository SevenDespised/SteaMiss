from PyQt6.QtCore import Qt, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QFont, QFontMetrics
from PyQt6.QtWidgets import QWidget

class SpeechBubble(QWidget):
    """
    显示在宠物下方的气泡对话框。
    """

    shown = pyqtSignal()
    hidden = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 无边框、置顶、工具窗口（不显示在任务栏）
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.text = ""
        self.bg_color = QColor(255, 255, 255, 240)
        self.border_color = QColor(200, 200, 200, 200)
        self.text_color = QColor(50, 50, 50)
        self.font_size = 10
        self.padding = 12
        self.max_width = 180
        self.pointer_height = 8
        self.pointer_width = 12
        
        # 自动隐藏定时器
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

    def show_message(self, text, duration=3000):
        """
        显示消息。
        @param text: 要显示的文本
        @param duration: 显示时长（毫秒），0 表示不自动隐藏
        """
        self.text = text
        self.adjust_size_to_text()
        self.show()
        self.update()

        # 每次显示/更新消息都发射 shown，便于“新气泡立刻切换上下文”
        self.shown.emit()
        
        if duration > 0:
            self.hide_timer.start(duration)
        else:
            self.hide_timer.stop()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.hidden.emit()

    def adjust_size_to_text(self):
        if not self.text:
            return
            
        font = QFont("Microsoft YaHei UI", self.font_size)
        metrics = QFontMetrics(font)
        
        # 计算文本包围盒
        rect = metrics.boundingRect(
            0, 0, self.max_width, 1000, 
            Qt.TextFlag.TextWordWrap, self.text
        )
        
        w = rect.width() + self.padding * 2
        h = rect.height() + self.padding * 2 + self.pointer_height
        
        self.resize(w, h)

    def paintEvent(self, event):
        if not self.text:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        ph = self.pointer_height
        pw = self.pointer_width
        
        # 绘制气泡路径
        path = QPainterPath()
        
        # 顶部尖角（指向宠物）
        center_x = w / 2
        path.moveTo(center_x, 0)
        path.lineTo(center_x + pw / 2, ph)
        
        # 右上角
        path.lineTo(w - 10, ph)
        path.arcTo(w - 20, ph, 20, 20, 90, -90)
        
        # 右下角
        path.lineTo(w, h - 10)
        path.arcTo(w - 20, h - 20, 20, 20, 0, -90)
        
        # 左下角
        path.lineTo(10, h)
        path.arcTo(0, h - 20, 20, 20, 270, -90)
        
        # 左上角
        path.lineTo(0, ph + 10)
        path.arcTo(0, ph, 20, 20, 180, -90)
        
        # 回到尖角左侧
        path.lineTo(center_x - pw / 2, ph)
        path.closeSubpath()
        
        # 填充背景和描边
        painter.setBrush(self.bg_color)
        painter.setPen(self.border_color)
        painter.drawPath(path)
        
        # 绘制文本
        painter.setPen(self.text_color)
        font = QFont("Microsoft YaHei UI", self.font_size)
        painter.setFont(font)
        
        text_rect = QRectF(
            self.padding, 
            ph + self.padding, 
            w - self.padding * 2, 
            h - ph - self.padding * 2
        )
        painter.drawText(
            text_rect, 
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, 
            self.text
        )
