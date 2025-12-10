import sys
import os
from PyQt6.QtWidgets import QWidget, QApplication, QMenu
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QAction, QCursor, QPixmap

# 引入新的管理器
from src.logic.behavior_manager import BehaviorManager
from src.logic.tool_manager import ToolManager
from src.logic.config_manager import ConfigManager
from src.logic.steam_manager import SteamManager
from src.logic.ui_manager import UIManager
from src.logic.resource_manager import ResourceManager
from src.logic.timer_manager import TimerManager
from src.ui.timer_overlay import TimerOverlay

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        
        # 1. 初始化窗口属性
        self.init_window()
        
        # 2. 初始化状态
        self.is_dragging = False
        self.drag_position = QPoint()
        
        # 3. 初始化管理器
        self.config_manager = ConfigManager()
        self.behavior_manager = BehaviorManager()
        self.steam_manager = SteamManager(self.config_manager)
        self.timer_manager = TimerManager()
        self.tool_manager = ToolManager(self.steam_manager, self.config_manager, self.timer_manager)
        
        # 初始化资源管理器 (一次性加载所有图片)
        self.resource_manager = ResourceManager()
        # 初始化计时器绘制器
        self.timer_overlay = TimerOverlay(self.timer_manager)
        
        # 初始化 UI 管理器
        self.ui_manager = UIManager(self.tool_manager, self.steam_manager, self.config_manager)
        self.ui_manager.get_radial_menu().hovered_changed.connect(self.on_menu_hover_changed)
        
        # 4. 核心循环 (大脑与心脏)
        self.current_state = "idle" # 当前行为状态
        self.frame_index = 0
        self.image = None
        
        # 初始刷新
        self.update_animation()
        
        # 这是一个“主循环”计时器，它驱动宠物的所有行为和动画
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(100) # 100ms = 10fps (逻辑帧率)

    def init_window(self):
        """初始化窗口设置"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(150, 150)
        self.center_window()

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # --- 核心循环 [接口] ---
    def game_loop(self):
        """
        主循环：每一帧都会执行
        这里将 逻辑(Brain) 和 渲染(View) 分离
        """
        # 1. 如果正在交互（比如悬停在菜单上），暂停 AI 思考
        # 这样 AI 不会突然把状态切回 idle
        if self.current_state == "point":
            pass 
        else:
            # 询问 BehaviorManager 下一步做什么
            new_state = self.behavior_manager.update(self.is_dragging)
            
            # 如果状态改变，重置帧索引
            if new_state != self.current_state:
                self.current_state = new_state
                self.frame_index = 0
            
        # 2. 决定怎么显示 (动画帧)
        self.update_animation()

    def update_animation(self):
        """
        [接口] 渲染层
        根据 current_state 更新图片帧
        """
        # 1. 如果不是静态交互状态(如point)，则让帧数前进
        if self.current_state != "point":
            self.frame_index = self.behavior_manager.get_next_frame(self.current_state, self.frame_index)
        
        # 2. 向仓库要图片 (这一步极快，因为是内存读取)
        self.image = self.resource_manager.get_frame(self.current_state, self.frame_index)
        
        # 3. 重绘
        self.update()

    # --- 交互事件 [接口] ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
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
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            event.accept()

    def mouseDoubleClickEvent(self, event):
        """
        [接口] 双击事件
        预留给：快速启动器、搜索框、或者唤醒功能
        """
        if event.button() == Qt.MouseButton.LeftButton:
            print("双击触发：可以在这里打开搜索框或启动器")
            # self.tool_manager.open_tool("launcher")
            event.accept()

    def contextMenuEvent(self, event):
        """
        右键点击事件
        """
        # 委托给 UI Manager 判断状态
        if self.ui_manager.is_radial_menu_just_closed():
            return

        if self.ui_manager.is_radial_menu_visible():
            self.ui_manager.close_radial_menu()
            return

        # 使用窗口中心作为菜单中心，确保宠物在圆环正中央
        center_pos = self.mapToGlobal(self.rect().center())
        self.ui_manager.show_radial_menu(center_pos)

    def on_menu_hover_changed(self, index):
        """
        当轮盘菜单悬停项改变时触发
        index: 悬停的菜单项索引，-1 表示无悬停
        """
        if index == -1:
            # 鼠标移开，恢复 AI 控制
            self.current_state = "idle"
            self.frame_index = 0
        else:
            # 鼠标悬停，强制切换到 point 状态
            # 这里 index 直接对应 point 图片的索引 (方向)
            self.current_state = "point"
            self.frame_index = index
            
        # 立即刷新一帧，保证响应速度
        self.update_animation()

    # --- 绘图 ---
    def paintEvent(self, event):
        """绘制事件：如果没有图片，画一个简单的圆形代表宠物"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 开启平滑图片变换，确保缩放后依然清晰
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self.image and not self.image.isNull():
            # 将图片绘制到整个窗口区域 (自动缩放)
            # 保持纵横比居中绘制
            target_rect = self.rect()
            
            # 计算保持比例的绘制区域
            scaled_size = self.image.size().scaled(target_rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
            x = (target_rect.width() - scaled_size.width()) // 2
            y = (target_rect.height() - scaled_size.height()) // 2
            draw_rect = target_rect.adjusted(x, y, -x, -y)
            # 实际上直接用 drawPixmap(x, y, w, h, pixmap) 更简单
            painter.drawPixmap(x, y, scaled_size.width(), scaled_size.height(), self.image)
        else:
            # 默认绘制一个可爱的圆形
            painter.setBrush(QColor(100, 180, 255, 200)) # 蓝色半透明
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, self.width(), self.height())
            
            # 画眼睛
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(35, 40, 30, 30)
            painter.drawEllipse(85, 40, 30, 30)
            
            painter.setBrush(QColor(0, 0, 0))
            painter.drawEllipse(45, 50, 10, 10)
            painter.drawEllipse(95, 50, 10, 10)
            
            # 画嘴巴
            painter.setPen(QColor(0, 0, 0))
            painter.drawArc(50, 80, 50, 30, 0, -180 * 16)

        # 绘制计时器（在宠物下方）
        self._paint_timer(painter)

    def _paint_timer(self, painter):
        if not hasattr(self, "timer_overlay"):
            return
        self.timer_overlay.draw(painter, self.rect())
