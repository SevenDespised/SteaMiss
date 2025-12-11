"""
路径菜单项构建器
"""
import os
from .base_builder import BaseMenuBuilder


class PathMenuBuilder(BaseMenuBuilder):
    """路径打开菜单项构建器"""
    
    def build(self):
        """构建路径菜单项"""
        paths = self.config_manager.get("explorer_paths", ["C:/", "C:/", "C:/"])
        aliases = self.config_manager.get("explorer_path_aliases", ["", "", ""])
        
        # 确保至少有3个路径
        while len(paths) < 3:
            paths.append("C:/")
        while len(aliases) < 3:
            aliases.append("")
        
        # 构建主选项
        main_label = self._format_path_for_display(paths[0], alias=aliases[0], is_main=True)
        path_item = {
            'key': 'open_path',
            'label': main_label,
            'callback': lambda: self.feature_manager.execute_action("open_path", path=paths[0])
        }
        
        # 构建子选项
        sub_items = []
        for i in range(1, 3):
            sub_label = self._format_path_for_display(paths[i], alias=aliases[i], is_main=False)
            sub_items.append({
                'label': sub_label,
                'callback': lambda p=paths[i]: self.feature_manager.execute_action("open_path", path=p)
            })
        
        path_item['sub_items'] = sub_items
        return path_item
    
    def _format_path_for_display(self, path, alias=None, is_main=True):
        """格式化路径显示"""
        if alias:
            trunc_alias = self._truncate_text(alias, max_len=8)
            if is_main:
                return f"打开:\n{trunc_alias}"
            else:
                return trunc_alias
        
        if not path:
            return "未设置"
        
        norm_path = os.path.normpath(path)
        parts = norm_path.split(os.sep)
        parts = [p for p in parts if p]
        
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
        else:
            if level2:
                return f"{level1}\n{level2}"
            else:
                return level1
