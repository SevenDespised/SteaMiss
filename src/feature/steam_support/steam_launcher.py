import os
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices

class SteamLauncher(QObject):
    """
    Steam 启动器
    负责与 Steam 客户端进行交互，如启动游戏、打开页面等
    """
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.steam_commands = {
            'store': 'steam://store',
            'community': 'steam://url/CommunityHome',
            'library': 'steam://nav/games',
            'workshop': 'steam://url/SteamWorkshop',
            'profile': 'steam://url/SteamIDEditPage',
            'downloads': 'steam://nav/downloads',
            'settings': 'steam://settings/'
        }
        
        self.web_urls = {
            'store': 'https://store.steampowered.com/',
            'community': 'https://steamcommunity.com/',
            'library': 'https://steamcommunity.com/my/games',
            'workshop': 'https://steamcommunity.com/workshop/',
            'profile': 'https://steamcommunity.com/my/profile/edit',
            'downloads': 'https://store.steampowered.com/account/',
            'settings': 'https://store.steampowered.com/account/'
        }

    def launch_game(self, appid):
        """启动 Steam 游戏"""
        if not appid: return
        try:
            os.startfile(f"steam://run/{appid}")
        except Exception as e:
            self.error_occurred.emit(f"Failed to launch game {appid}: {e}")

    def open_page(self, page_type):
        """
        打开 Steam 页面
        page_type: 'library', 'community', 'store', 'workshop', 'profile', 'downloads', 'settings'
        """
        cmd = self.steam_commands.get(page_type)
        url = self.web_urls.get(page_type)
        
        if cmd:
            try:
                os.startfile(cmd)
            except Exception as e:
                # 如果 steam 协议失败，尝试打开网页
                if url:
                    QDesktopServices.openUrl(QUrl(url))
                else:
                    self.error_occurred.emit(f"Failed to open steam command {cmd}: {e}")
        elif url:
            QDesktopServices.openUrl(QUrl(url))
