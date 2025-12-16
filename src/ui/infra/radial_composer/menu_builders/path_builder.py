"""
路径菜单项构建器。
"""

import os

from src.ui.infra.radial_composer.menu_builders.base_builder import BaseMenuBuilder
from src.feature_core.app.actions import Action


class PathMenuBuilder(BaseMenuBuilder):
    """路径打开菜单项构建器"""

    def build(self):
        """构建路径菜单项"""
        # 注意：ConfigManager.get() 直接返回 settings 内部对象的引用（可变 list）。
        # 若在这里对 list 做 append，会“就地修改配置”，导致后续菜单闭包读取到陈旧/错位数据。
        # 因此必须在 build 时创建快照（copy），并只在快照上做补齐与回调捕获。
        raw_paths = self.config_manager.get("explorer_paths", ["C:/", "C:/", "C:/"])
        raw_aliases = self.config_manager.get("explorer_path_aliases", ["", "", ""])

        paths = list(raw_paths) if isinstance(raw_paths, list) else ["C:/", "C:/", "C:/"]
        aliases = list(raw_aliases) if isinstance(raw_aliases, list) else ["", "", ""]

        # 固定输出 3 个槽位（主 + 2 个子项），不足则补齐默认值；不修改原配置。
        while len(paths) < 3:
            paths.append("C:/")
        while len(aliases) < 3:
            aliases.append("")

        normalized_paths: list[str] = []
        normalized_aliases: list[str] = []
        for p, a in zip(paths[:3], aliases[:3]):
            has_real_path = isinstance(p, str) and bool(p.strip())
            normalized_paths.append(p.strip() if has_real_path else "C:/")
            # 未配置路径时不允许设置别名，避免 UI 显示与行为不一致
            normalized_aliases.append(a if (has_real_path and isinstance(a, str)) else "")

        # 使用不可变快照，避免后续对 paths/aliases 的任何修改影响已创建回调
        path_snapshot = tuple(normalized_paths)
        alias_snapshot = tuple(normalized_aliases)

        main_path = path_snapshot[0]
        main_label = self._format_path_for_display(main_path, alias=alias_snapshot[0], is_main=True)
        path_item = {
            "key": "open_path",
            "label": main_label,
            # 用默认参数捕获“值快照”，避免闭包引用可变 list
            "callback": (lambda p=main_path: self.action_bus.execute(Action.OPEN_PATH, path=p)),
        }

        sub_items = []
        for p, a in zip(path_snapshot[1:3], alias_snapshot[1:3]):
            sub_label = self._format_path_for_display(p, alias=a, is_main=False)
            sub_items.append(
                {
                    "label": sub_label,
                    "callback": (lambda p=p: self.action_bus.execute(Action.OPEN_PATH, path=p)),
                }
            )

        path_item["sub_items"] = sub_items
        return path_item

    def _format_path_for_display(self, path, alias=None, is_main=True):
        """格式化路径显示"""
        if alias:
            trunc_alias = self._truncate_text(alias, max_len=8)
            return f"打开：\n{trunc_alias}" if is_main else trunc_alias

        if not path:
            return "未设置"

        norm_path = os.path.normpath(path)
        parts = [p for p in norm_path.split(os.sep) if p]
        if not parts:
            return path

        level1 = parts[0]
        level2 = ""
        has_more = len(parts) > 2

        if len(parts) > 1:
            level2 = self._truncate_text(parts[1], max_len=4)
            if has_more:
                level2 += "..."

        if is_main:
            display = f"打开:\n{level1}"
            if level2:
                display += f"{os.sep}{level2}"
            elif has_more:
                display += f"{os.sep}..."
            return display

        return f"{level1}\n{level2}" if level2 else level1


__all__ = ["PathMenuBuilder"]


