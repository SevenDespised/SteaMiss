"""
Steam 页面菜单项构建器。
"""

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder


class SteamPageMenuBuilder(BaseMenuBuilder):
    """Steam 页面菜单项构建器"""

    PAGE_TYPES = {
        "library": "游戏库",
        "store": "商店",
        "community": "社区",
        "workshop": "创意工坊",
        "profile": "个人资料",
        "downloads": "下载",
        "settings": "设置",
    }

    def build(self):
        selected_pages = self.config_manager.get("steam_menu_pages", ["library", "store", "community"])

        while len(selected_pages) < 3:
            selected_pages.append("library")
        selected_pages = selected_pages[:3]

        default_pages = ["library", "store", "community"]
        for i in range(3):
            if selected_pages[i] is None or selected_pages[i] not in self.PAGE_TYPES:
                selected_pages[i] = default_pages[i]

        main_page = selected_pages[0]
        main_label = self.PAGE_TYPES.get(main_page, main_page)

        steam_page_item = {
            "key": "open_steam_page",
            "label": f"跳转：\n{main_label}",
            "callback": (lambda p=main_page: self.feature_router.execute_action("open_steam_page", page_type=p)),
        }

        sub_items = []
        for i in range(1, 3):
            page = selected_pages[i]
            label = self.PAGE_TYPES.get(page, page)
            sub_items.append(
                {"label": label, "callback": (lambda p=page: self.feature_router.execute_action("open_steam_page", page_type=p))}
            )

        steam_page_item["sub_items"] = sub_items
        return steam_page_item


__all__ = ["SteamPageMenuBuilder"]


