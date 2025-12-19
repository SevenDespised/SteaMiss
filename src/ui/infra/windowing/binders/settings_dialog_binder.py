from __future__ import annotations

from src.ui.infra.windowing.context import WindowContext


class SettingsDialogBinder:
    """SettingsDialog 绑定器：加载配置、保存配置、游戏搜索联动。"""

    def bind(self, view: object, ctx: WindowContext) -> None:
        # 1) 加载配置
        view.load_settings(ctx.config_manager.settings)

        # 2) 保存请求
        def handle_save(settings: dict) -> None:
            # 保存前记录账号相关字段，便于判断是否需要刷新 Steam 凭证
            old_api_key = ctx.config_manager.get("steam_api_key")
            old_steam_id = ctx.config_manager.get("steam_id")
            old_alt_ids = ctx.config_manager.get("steam_alt_ids", [])

            # 批量更新配置，避免多次 IO
            ctx.config_manager.update_dict(settings)

            # 账号凭证变更：仅做“失效 + 重新抓取 games/summary”，不清理旧 cache，也不自动抓取慢接口
            new_api_key = ctx.config_manager.get("steam_api_key")
            new_steam_id = ctx.config_manager.get("steam_id")
            new_alt_ids = ctx.config_manager.get("steam_alt_ids", [])
            if (new_api_key != old_api_key) or (new_steam_id != old_steam_id) or (new_alt_ids != old_alt_ids):
                try:
                    ctx.steam_manager.on_credentials_changed()
                except Exception:
                    pass

        view.request_save.connect(handle_save)

        # 3) 游戏搜索请求：先缓存搜索；无结果则触发异步更新
        def handle_search(keyword: str) -> None:
            results = ctx.steam_manager.search_games(keyword)
            if not results:
                ctx.steam_manager.fetch_games_stats()
            view.update_search_results(results)

        view.request_search_games.connect(handle_search)


__all__ = ["SettingsDialogBinder"]


