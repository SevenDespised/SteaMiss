"""
桌宠主窗口：负责动画/交互/绘制，并通过注入的 TimerOverlay 绘制计时器。
"""

from PyQt6.QtCore import QPoint, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QPainter
from PyQt6.QtWidgets import QApplication, QWidget

from src.ui.widgets.speech_bubble import SpeechBubble


class DesktopPet(QWidget):
    """
    桌宠窗口（置顶、无边框、可拖拽）。

    约定：
    - 交互信号只表达“意图”，外部通过 Handler/Binder 接线；
    - 计时器绘制由注入的 overlay 负责，避免 DesktopPet 了解计时器业务。
    """

    # 定义信号，用于通知状态变化
    visibility_changed = pyqtSignal(bool)
    topmost_changed = pyqtSignal(bool)

    # 交互信号
    right_clicked = pyqtSignal(QPoint)
    double_clicked = pyqtSignal()

    def __init__(self, behavior_manager, resource_manager, timer_overlay):
        """
        @param behavior_manager: BehaviorManager（提供行为状态与帧推进）
        @param resource_manager: ResourceManager（提供图片帧）
        @param timer_overlay: TimerOverlay（绘制计时器覆盖层）
        """
        super().__init__()

        # 1. 初始化窗口属性
        self.init_window()

        # 2. 初始化状态
        self.is_dragging = False
        self.drag_position = QPoint()

        # 3. 注入依赖
        self.behavior_manager = behavior_manager
        self.resource_manager = resource_manager
        self.timer_overlay = timer_overlay

        # 监听行为管理器的说话请求
        self.behavior_manager.speech_requested.connect(self.say)
        self.behavior_manager.speech_stream_started.connect(self.say_stream_started)
        self.behavior_manager.speech_stream_delta.connect(self.say_stream_delta)
        self.behavior_manager.speech_stream_done.connect(self.say_stream_done)

        # 初始化气泡对话框
        self.speech_bubble = SpeechBubble()
        self.speech_bubble.shown.connect(self._on_bubble_shown)
        self.speech_bubble.hidden.connect(self._on_bubble_hidden)

        # 4. 核心循环 (大脑与心脏)
        self.current_state = "idle"  # 当前行为状态
        self.frame_index = 0
        self.image = None

        # 初始刷新
        self.update_animation()

        # 主循环计时器（驱动行为与动画）
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(100)  # 100ms = 10fps (逻辑帧率)

    def init_window(self):
        """初始化窗口设置"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(150, 150)
        self.center_window()

    def is_topmost(self):
        return bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)

    def set_topmost(self, enable: bool):
        flags = self.windowFlags()
        if enable:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint

        if flags != self.windowFlags():
            self.setWindowFlags(flags)
            self.show()  # 更改 flags 后需要 show 才能生效
            self.activateWindow()  # 防止失去焦点导致交互失效
            self.topmost_changed.emit(enable)
            
            # 同步气泡层级
            if hasattr(self, 'speech_bubble'):
                was_visible = self.speech_bubble.isVisible()
                self.speech_bubble.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enable)
                if was_visible:
                    self.speech_bubble.show()

    def toggle_topmost(self):
        self.set_topmost(not self.is_topmost())

    def set_visibility(self, visible: bool):
        if visible:
            self.show()
        else:
            self.hide()
        # 信号由 showEvent/hideEvent 触发

    def showEvent(self, event):
        super().showEvent(event)
        self.visibility_changed.emit(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.visibility_changed.emit(False)
        if hasattr(self, 'speech_bubble'):
            self.speech_bubble.hide()

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # --- 核心循环 ---
    def game_loop(self):
        """
        主循环：每一帧都会执行
        这里将 逻辑(Brain) 和 渲染(View) 分离
        """
        # 1) 悬停菜单时暂停 AI 思考，避免突然切状态
        if self.current_state != "point":
            new_state = self.behavior_manager.update(self.is_dragging)
            if new_state != self.current_state:
                self.current_state = new_state
                self.frame_index = 0

        # 2) 渲染动画帧
        self.update_animation()

    def update_animation(self):
        """
        根据 current_state 更新图片帧并触发重绘
        """
        if self.current_state != "point":
            self.frame_index = self.behavior_manager.get_next_frame(self.current_state, self.frame_index)

        self.image = self.resource_manager.get_frame(self.current_state, self.frame_index)
        self.update()

    def say(self, text, duration=10000):
        """让宠物说话（显示气泡）"""
        self.speech_bubble.show_message(text, duration)
        self._update_bubble_position()
        # 确保气泡层级正确
        self.speech_bubble.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.is_topmost())
        self.speech_bubble.show()

    def say_stream_started(self, request_id: str):
        self.speech_bubble.start_stream(request_id, duration_after_done=10000)
        self._update_bubble_position()
        self.speech_bubble.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.is_topmost())
        self.speech_bubble.show()

    def say_stream_delta(self, request_id: str, delta: str):
        self.speech_bubble.append_stream(request_id, delta)
        self._update_bubble_position()

    def say_stream_done(self, request_id: str):
        self.speech_bubble.end_stream(request_id)

    def _on_bubble_shown(self):
        # 新气泡出现时立刻切换上下文：
        # - 有 pending ctx：应用
        # - 无 pending ctx：清空（回到默认互动项）
        ctx = self.behavior_manager.consume_pending_interaction_context()
        if ctx is None:
            self.behavior_manager.clear_interaction_context()
        else:
            self.behavior_manager.set_interaction_context(ctx)

    def _on_bubble_hidden(self):
        # 只要没有气泡就清上下文
        self.behavior_manager.clear_interaction_context()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._update_bubble_position()

    def _update_bubble_position(self):
        if hasattr(self, 'speech_bubble') and self.speech_bubble.isVisible():
            geo = self.geometry()
            bubble_geo = self.speech_bubble.geometry()
            x = geo.x() + (geo.width() - bubble_geo.width()) // 2
            y = geo.y() + geo.height() + 5  # 5px margin
            self.speech_bubble.move(x, y)

    # --- 交互事件 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.behavior_manager.set_paused("dragging", True)
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.behavior_manager.set_paused("dragging", False)
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            event.accept()

    def mouseDoubleClickEvent(self, event):
        """双击事件：由外部接线决定触发什么功能"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
            event.accept()

    def contextMenuEvent(self, event):
        """右键点击：以窗口中心作为菜单中心，确保宠物在圆环正中央"""
        center_pos = self.mapToGlobal(self.rect().center())
        self.right_clicked.emit(center_pos)

    def on_menu_hover_changed(self, index):
        """
        当轮盘菜单悬停项改变时触发
        @param index: 悬停的菜单项索引，-1 表示无悬停
        """
        if index == -1:
            self.current_state = "idle"
            self.frame_index = 0
            self.behavior_manager.set_paused("menu_hover", False)
        else:
            self.current_state = "point"
            self.frame_index = index
            self.behavior_manager.set_paused("menu_hover", True)
        self.update_animation()

    # --- 绘图 ---
    def paintEvent(self, event):
        """绘制事件：如果没有图片，画一个简单的圆形代表宠物"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self.image and not self.image.isNull():
            target_rect = self.rect()
            scaled_size = self.image.size().scaled(target_rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
            x = (target_rect.width() - scaled_size.width()) // 2
            y = (target_rect.height() - scaled_size.height()) // 2
            painter.drawPixmap(x, y, scaled_size.width(), scaled_size.height(), self.image)
        else:
            painter.setBrush(QColor(100, 180, 255, 200))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, self.width(), self.height())

        self._paint_timer(painter)

    def _paint_timer(self, painter):
        if not hasattr(self, "timer_overlay"):
            return
        self.timer_overlay.draw(painter, self.rect())


__all__ = ["DesktopPet"]


