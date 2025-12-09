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
from src.ui.radial_menu import RadialMenu

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
        # ToolManager 需要 SteamManager 来创建统计窗口
        self.tool_manager = ToolManager(self.steam_manager)
        
        # 初始化轮盘菜单
        self.radial_menu = RadialMenu()
        
        # 4. 核心循环 (大脑与心脏)
        self.current_state = "idle" # 当前行为状态
        self.frame_index = 0
        
        # 这是一个“主循环”计时器，它驱动宠物的所有行为和动画
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(100) # 100ms = 10fps (逻辑帧率)
        
        # 资源加载
        self.image = None 
        self.load_image("assets/main.jpg") 

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

    def load_image(self, path):
        self.image = QPixmap(path)
        if not self.image.isNull():
            # 强制缩放到 150x150 (保持纵横比，平滑缩放)
            target_size = 150
            self.image = self.image.scaled(
                target_size, target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.resize(self.image.size())
            self.update()

    # --- 核心循环 [接口] ---
    def game_loop(self):
        """
        主循环：每一帧都会执行
        这里将 逻辑(Brain) 和 渲染(View) 分离
        """
        # 1. 询问 BehaviorManager 下一步做什么
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
        # 询问 BehaviorManager 下一帧是第几帧
        self.frame_index = self.behavior_manager.get_next_frame(self.current_state, self.frame_index)
        
        # self.image = self.animations[self.current_state][self.frame_index]
        self.update() # 触发 paintEvent 重绘

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
        这里不再直接写死菜单，而是调用一个“展示交互面板”的方法
        """
        # 使用窗口中心作为菜单中心，确保宠物在圆环正中央
        center_pos = self.mapToGlobal(self.rect().center())
        self.show_interaction_panel(center_pos)

    def _truncate_game_name(self, name, max_len=8):
        """
        截断游戏名称，限制显示长度
        规则：最多 max_len 个英文字符，1个中文字符 = 2个英文字符
        如果超出，保留 max_len-2 的长度并添加 ".."
        """
        # 1. 计算总长度
        total_len = 0
        for char in name:
            total_len += 2 if '\u4e00' <= char <= '\u9fff' else 1
        
        if total_len <= max_len:
            return name
            
        # 2. 需要截断
        target_len = max_len
        current_len = 0
        result = ""
        for char in name:
            char_len = 2 if '\u4e00' <= char <= '\u9fff' else 1
            if current_len + char_len > target_len:
                break
            current_len += char_len
            result += char
            
        return result + ".."

    def show_interaction_panel(self, position):
        """
        [接口] 交互面板入口
        目前是普通菜单，未来可以替换为 Radial Menu (轮盘) 或自定义 Widget
        """
        # 获取配置的路径
        explorer_path = self.config_manager.get("explorer_path", "C:/")
        
        # 格式化显示路径 (前两级)
        display_path = explorer_path
        try:
            norm_path = os.path.normpath(explorer_path)
            parts = norm_path.split(os.sep)
            # 处理盘符情况 (e.g. "C:" "Users" ...)
            if len(parts) > 2:
                display_path = os.sep.join(parts[:2])
        except:
            pass
            
        open_label = f"打开\n{display_path}"

        # --- 轮盘菜单实现 ---
        # 定义排序顺序 (key)
        order = [
            "launch_recent",   # 启动游戏(最近)
            "say_hello",       # 打招呼
            "discounts",       # 特惠信息
            "exit",            # 退出
            "stats",           # 游玩记录
            "open_path",       # 打开文件路径
            "launch_favorite"  # 启动最爱
        ]

        # 收集所有可能的菜单项
        all_items = []

        # 1. 基础功能
        all_items.append({'key': 'say_hello', 'label': '打招呼', 'callback': self.say_hello})
        all_items.append({'key': 'stats', 'label': '游玩记录', 'callback': lambda: self.tool_manager.open_tool("stats")})
        all_items.append({'key': 'discounts', 'label': '特惠推荐', 'callback': lambda: self.tool_manager.open_tool("discounts")})
        all_items.append({'key': 'open_path', 'label': open_label, 'callback': self.open_explorer})
        all_items.append({'key': 'exit', 'label': '退出', 'callback': QApplication.instance().quit})
        
        # 2. Steam 游戏扩展
        recent_game = self.steam_manager.get_recent_game()
        if recent_game:
            name = recent_game.get("name", "Unknown")
            name = self._truncate_game_name(name)
            all_items.append({
                'key': 'launch_recent',
                'label': f"最近\n{name}",
                'callback': lambda: self.launch_steam_game(recent_game['appid'])
            })
            
        fav_game = self.config_manager.get("steam_favorite_game")
        if fav_game:
            name = fav_game.get("name", "Unknown")
            name = self._truncate_game_name(name)
            all_items.append({
                'key': 'launch_favorite',
                'label': f"启动\n{name}",
                'callback': lambda: self.launch_steam_game(fav_game['appid'])
            })

        # 3. 按照预定顺序排序
        items_map = {item['key']: item for item in all_items}
        sorted_items = []
        for key in order:
            if key in items_map:
                sorted_items.append(items_map[key])
        
        self.radial_menu.set_items(sorted_items)
        self.radial_menu.show_at(position)

    # --- 功能实现区 ---
    def say_hello(self):
        # 从配置中读取打招呼内容
        content = self.config_manager.get("say_hello_content", "你好！")
        print(content)

    def open_explorer(self):
        path = self.config_manager.get("explorer_path", "C:/")
        if os.path.exists(path):
            os.startfile(path)
        else:
            print(f"Path not found: {path}")

    def launch_steam_game(self, appid):
        """启动 Steam 游戏"""
        try:
            os.startfile(f"steam://run/{appid}")
        except Exception as e:
            print(f"Failed to launch game {appid}: {e}")

    # --- 绘图 ---
    def paintEvent(self, event):
        """绘制事件：如果没有图片，画一个简单的圆形代表宠物"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.image and not self.image.isNull():
            painter.drawPixmap(0, 0, self.image)
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
