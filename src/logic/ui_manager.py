import os
from PyQt6.QtCore import QPoint
from src.ui.radial_menu import RadialMenu

class UIManager:
    def __init__(self, tool_manager, steam_manager, config_manager):
        self.tool_manager = tool_manager
        self.steam_manager = steam_manager
        self.config_manager = config_manager
        
        # 管理的 UI 组件
        self.radial_menu = RadialMenu()
        
    def get_radial_menu(self):
        """提供给 Pet 用于事件连接 (如 hover)"""
        return self.radial_menu

    def show_radial_menu(self, center_pos: QPoint):
        """
        构建并显示环形菜单
        """
        # 1. 获取菜单项数据
        items = self._build_menu_items()
        
        # 2. 设置并显示
        self.radial_menu.set_items(items)
        self.radial_menu.show_at(center_pos)

    def close_radial_menu(self):
        if self.radial_menu.isVisible():
            self.radial_menu.close()

    def is_radial_menu_visible(self):
        return self.radial_menu.isVisible()
        
    def is_radial_menu_just_closed(self):
        return getattr(self.radial_menu, 'just_closed', False)

    def _build_menu_items(self):
        """
        内部方法：构建排序好的菜单项列表
        """
        # 定义排序顺序
        order = [
            "launch_recent", "say_hello", "discounts", 
            "timer", "stats", "open_path", "launch_favorite"
        ]
        
        all_items = []

        # --- 生成各个菜单项 ---
        
        # 1. 路径打开
        path_label = self._get_formatted_path_label()
        all_items.append({'key': 'open_path', 'label': path_label, 'callback': lambda: self.tool_manager.execute_action("open_path")})
        
        # 2. 基础功能
        all_items.append({'key': 'say_hello', 'label': '打招呼', 'callback': lambda: self.tool_manager.execute_action("say_hello")})
        all_items.append({'key': 'stats', 'label': '游玩记录', 'callback': lambda: self.tool_manager.open_tool("stats")})
        all_items.append({'key': 'discounts', 'label': '特惠推荐', 'callback': lambda: self.tool_manager.open_tool("discounts")})
        # 退出替换为计时器
        all_items.append(self._build_timer_item())

        # 3. Steam 动态项
        recent_game = self.steam_manager.get_recent_game()
        if recent_game:
            name = self._truncate_text(recent_game.get("name", "Unknown"))
            all_items.append({
                'key': 'launch_recent',
                'label': f"最近\n{name}",
                'callback': lambda: self.tool_manager.execute_action("launch_game", appid=recent_game['appid'])
            })

        fav_game = self.config_manager.get("steam_favorite_game")
        if fav_game:
            name = self._truncate_text(fav_game.get("name", "Unknown"))
            all_items.append({
                'key': 'launch_favorite',
                'label': f"启动\n{name}",
                'callback': lambda: self.tool_manager.execute_action("launch_game", appid=fav_game['appid'])
            })

        # --- 排序 ---
        items_map = {item['key']: item for item in all_items}
        sorted_items = []
        for key in order:
            if key in items_map:
                sorted_items.append(items_map[key])
                
        return sorted_items

    def _build_timer_item(self):
        """根据计时状态构造菜单项。"""
        label = "开始\n计时"
        if getattr(self.tool_manager, "timer_manager", None):
            if self.tool_manager.timer_manager.is_running():
                label = "结束\n计时"
        return {
            'key': 'timer',
            'label': label,
            'callback': lambda: self.tool_manager.execute_action("toggle_timer")
        }

    def _truncate_text(self, text, max_len=8):
        """文本截断工具"""
        total_len = 0
        for char in text:
            total_len += 2 if '\u4e00' <= char <= '\u9fff' else 1
        
        if total_len <= max_len:
            return text
            
        target_len = max_len
        current_len = 0
        result = ""
        for char in text:
            char_len = 2 if '\u4e00' <= char <= '\u9fff' else 1
            if current_len + char_len > target_len:
                break
            current_len += char_len
            result += char
            
        return result + ".."

    def _get_formatted_path_label(self):
        """获取格式化的路径标签"""
        explorer_path = self.config_manager.get("explorer_path", "C:/")
        display_path = explorer_path
        try:
            norm_path = os.path.normpath(explorer_path)
            parts = norm_path.split(os.sep)
            if len(parts) > 2:
                display_path = os.sep.join(parts[:2])
        except:
            pass
        return f"打开\n{display_path}"
