"""
Steam 游戏菜单项构建器。
"""

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder


class SteamGameMenuBuilder(BaseMenuBuilder):
    """Steam 游戏相关菜单项构建器"""

    def __init__(self, feature_router, config_manager, steam_manager):
        super().__init__(feature_router, config_manager)
        self.steam_manager = steam_manager

    def build_recent_game_item(self):
        recent_games = self.steam_manager.get_recent_games(3)
        if not recent_games:
            return None

        top1 = recent_games[0]
        name = self._truncate_text(top1.get("name", "Unknown"))
        top1_appid = top1.get("appid")
        item = {
            "key": "launch_recent",
            "label": f"最近：\n{name}",
            # 主项也使用默认参数捕获，避免闭包对外部变量引用不一致
            "callback": (lambda appid=top1_appid: self.feature_router.execute_action("launch_game", appid=appid)),
        }

        if len(recent_games) > 1:
            sub_items = []
            for game in recent_games[1:]:
                sub_name = self._truncate_text(game.get("name", "Unknown"))
                sub_items.append(
                    {"label": sub_name, "callback": (lambda g=game: self.feature_router.execute_action("launch_game", appid=g["appid"]))}
                )
            item["sub_items"] = sub_items

        return item

    def build_quick_launch_item(self):
        quick_launch_games = self.config_manager.get("steam_quick_launch_games", [None, None, None])
        if not isinstance(quick_launch_games, list):
            quick_launch_games = [None, None, None]

        recent_games = self.steam_manager.get_recent_games(10)
        final_games = self._merge_configured_and_recent(quick_launch_games, recent_games)
        if not final_games:
            return None

        top1 = final_games[0]
        name = self._truncate_text(top1.get("name", "Unknown"))
        top1_appid = top1.get("appid")
        item = {
            "key": "launch_favorite",
            "label": f"启动：\n{name}",
            # 主项也使用默认参数捕获，避免闭包对外部变量引用不一致
            "callback": (lambda appid=top1_appid: self.feature_router.execute_action("launch_game", appid=appid)),
        }

        if len(final_games) > 1:
            sub_items = []
            for game in final_games[1:]:
                sub_name = self._truncate_text(game.get("name", "Unknown"))
                sub_items.append(
                    {"label": sub_name, "callback": (lambda g=game: self.feature_router.execute_action("launch_game", appid=g["appid"]))}
                )
            item["sub_items"] = sub_items

        return item

    def _merge_configured_and_recent(self, configured, recent):
        final_games = []
        used_appids = set()

        for game in configured:
            if game:
                final_games.append(game)
                used_appids.add(game["appid"])
            else:
                final_games.append(None)

        recent_idx = 0
        for i in range(3):
            if final_games[i] is None:
                while recent_idx < len(recent):
                    candidate = recent[recent_idx]
                    recent_idx += 1
                    if candidate["appid"] not in used_appids:
                        final_games[i] = candidate
                        used_appids.add(candidate["appid"])
                        break

        return [g for g in final_games if g is not None]


__all__ = ["SteamGameMenuBuilder"]


