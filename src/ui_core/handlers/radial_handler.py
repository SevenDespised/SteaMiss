from PyQt6.QtCore import QPoint, QObject, pyqtSignal
from src.ui.radial_menu import RadialMenu

class RadialHandler(QObject):
    """
    UI管理器
    负责协调各个菜单项构建器，生成环形菜单
    负责管理所有子窗口的生命周期
    """
    
    menu_hovered_changed = pyqtSignal(int)

    def __init__(self, menu_composer):
        super().__init__()
        self.menu_composer = menu_composer
        # 管理的 UI 组件
        self.radial_menu = RadialMenu()
        self.radial_menu.hovered_changed.connect(self.menu_hovered_changed)

    def handle_right_click(self, center_pos: QPoint):
        """
        处理右键点击事件：决定是显示还是关闭菜单
        """
        if self.is_radial_menu_just_closed():
            return

        if self.is_radial_menu_visible():
            self.close_radial_menu()
            return

        self.show_radial_menu(center_pos)
        
    def show_radial_menu(self, center_pos: QPoint):
        """
        构建并显示环形菜单
        """
        # 1. 获取菜单项数据
        items = self.menu_composer.compose()
        
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