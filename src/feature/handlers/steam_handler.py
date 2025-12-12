import os

class SteamFeatureHandler:
    def __init__(self, steam_manager):
        self.steam_manager = steam_manager

    def launch_game(self, appid=None, **kwargs):
        if not appid: return
        self.steam_manager.launch_game(appid)

    def open_steam_page(self, page_type=None, **kwargs):
        """
        打开Steam页面
        page_type: 'library', 'community', 'store', 'workshop', 'profile', 'downloads', 'settings'
        """
        if not page_type: return
        self.steam_manager.open_page(page_type)

