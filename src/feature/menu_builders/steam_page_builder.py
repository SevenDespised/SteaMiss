"""
Steam页面菜单项构建器
"""
from .base_builder import BaseMenuBuilder


class SteamPageMenuBuilder(BaseMenuBuilder):
    """Steam页面菜单项构建器"""
    
    PAGE_TYPES = {
        'library': '游戏库',
        'store': '商店',
        'community': '社区',
        'workshop': '创意工坊',
        'profile': '个人资料',
        'friends': '好友',
        'downloads': '下载',
        'settings': '设置'
    }
    
    def build(self):
        """构建Steam页面菜单项"""
        selected_pages = self.config_manager.get("steam_menu_pages", ['library', 'store', 'community'])
        
        # 确保有3个页面
        while len(selected_pages) < 3:
            selected_pages.append('library')
        selected_pages = selected_pages[:3]
        
        # 过滤掉None值，使用默认值
        default_pages = ['library', 'store', 'community']
        for i in range(3):
            if selected_pages[i] is None or selected_pages[i] not in self.PAGE_TYPES:
                selected_pages[i] = default_pages[i]
        
        # 构建主选项
        main_page = selected_pages[0]
        main_label = self.PAGE_TYPES.get(main_page, main_page)
        
        steam_page_item = {
            'key': 'open_steam_page',
            'label': f'Steam\n{main_label}',
            'callback': lambda p=main_page: self.feature_manager.execute_action("open_steam_page", page_type=p)
        }
        
        # 构建子选项
        sub_items = []
        for i in range(1, 3):
            page = selected_pages[i]
            label = self.PAGE_TYPES.get(page, page)
            sub_items.append({
                'label': label,
                'callback': lambda p=page: self.feature_manager.execute_action("open_steam_page", page_type=p)
            })
        
        steam_page_item['sub_items'] = sub_items
        return steam_page_item
