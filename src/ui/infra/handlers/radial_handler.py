from PyQt6.QtCore import QPoint, QObject, pyqtSignal

from src.ui.widgets.radial_menu import RadialMenu


class RadialHandler(QObject):
    """
    轮盘菜单管理器：负责协调菜单构建器，生成并展示环形菜单。
    """

    menu_hovered_changed = pyqtSignal(int)

    def __init__(self, menu_composer):
        super().__init__()
        self.menu_composer = menu_composer
        self.radial_menu = RadialMenu()
        self.radial_menu.hovered_changed.connect(self.menu_hovered_changed)
        self._last_center_pos = None

    def handle_right_click(self, center_pos: QPoint):
        """处理右键点击事件：决定显示还是关闭菜单"""
        if self.is_radial_menu_just_closed():
            return
        if self.is_radial_menu_visible():
            self.close_radial_menu()
            return
        self.show_radial_menu(center_pos)

    def show_radial_menu(self, center_pos: QPoint):
        self._last_center_pos = center_pos
        items = self.menu_composer.compose()
        self.radial_menu.set_items(items)
        self.radial_menu.show_at(center_pos)

    def refresh_menu(self):
        """若菜单正在显示，则重建并刷新菜单项（用于气泡 show/hide 同步菜单）。"""
        if not self.is_radial_menu_visible():
            return
        items = self.menu_composer.compose()
        self.radial_menu.set_items(items)
        if self._last_center_pos is not None:
            self.radial_menu.show_at(self._last_center_pos)
        else:
            self.radial_menu.update()

    def close_radial_menu(self):
        if self.radial_menu.isVisible():
            self.radial_menu.close()

    def is_radial_menu_visible(self):
        return self.radial_menu.isVisible()

    def is_radial_menu_just_closed(self):
        return getattr(self.radial_menu, "just_closed", False)


__all__ = ["RadialHandler"]


