from __future__ import annotations

from src.ui.infra.windowing.context import WindowContext


class SettingsDialogBinder:
    """SettingsDialog 绑定器：加载配置、保存配置、游戏搜索联动。"""

    def bind(self, view: object, ctx: WindowContext) -> None:
        # 1) 加载配置
        view.load_settings(ctx.config_manager.settings)

        # 2) 保存请求
        def handle_save(settings: dict) -> None:
            for key, value in settings.items():
                ctx.config_manager.set(key, value)

        view.request_save.connect(handle_save)

        # 3) 游戏搜索请求：先缓存搜索；无结果则触发异步更新
        def handle_search(keyword: str) -> None:
            results = ctx.steam_manager.search_games(keyword)
            if not results:
                ctx.steam_manager.fetch_games_stats()
            view.update_search_results(results)

        view.request_search_games.connect(handle_search)


__all__ = ["SettingsDialogBinder"]


