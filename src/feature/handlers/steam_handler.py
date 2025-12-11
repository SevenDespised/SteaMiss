import os

class SteamFeatureHandler:
    def __init__(self, steam_manager):
        self.steam_manager = steam_manager

    def launch_game(self, appid=None, **kwargs):
        if not appid: return
        try:
            os.startfile(f"steam://run/{appid}")
        except Exception as e:
            raise Exception(f"Failed to launch game {appid}: {e}")

    def open_steam_page(self, page_type=None, **kwargs):
        """
        page_type: 'library', 'community', 'store', 'workshop'
        """
        steam_commands = {
            'store': 'steam://store',
            'community': 'steam://url/CommunityHome',
            'library': 'steam://nav/games',
            'workshop': 'steam://url/SteamWorkshop'
        }
        
        web_urls = {
            'store': 'https://store.steampowered.com/',
            'community': 'https://steamcommunity.com/',
            'library': 'https://steamcommunity.com/my/games',
            'workshop': 'https://steamcommunity.com/workshop/'
        }
        
        cmd = steam_commands.get(page_type)
        url = web_urls.get(page_type)
        
        if cmd:
            try:
                os.startfile(cmd)
            except Exception as e:
                # 如果 steam 协议失败，尝试打开网页
                if url:
                    import webbrowser
                    webbrowser.open(url)
                else:
                    raise Exception(f"Failed to open steam command {cmd}: {e}")
        elif url:
            import webbrowser
            webbrowser.open(url)
