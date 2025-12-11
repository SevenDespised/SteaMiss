"""
基础菜单项构建器
"""

class BaseMenuBuilder:
    """菜单项构建器基类"""
    
    def __init__(self, feature_manager, config_manager):
        self.feature_manager = feature_manager
        self.config_manager = config_manager
    
    def build(self):
        """构建菜单项，子类必须实现"""
        raise NotImplementedError
    
    def _truncate_text(self, text, max_len=8):
        """文本截断工具"""
        total_len = 0
        for char in text:
            total_len += 2 if '\u4e00' <= char <= '\u9fff' else 1
        
        if total_len <= max_len:
            return text
            
        target_len = max_len
        current_len = 0
        result = ""
        for char in text:
            char_len = 2 if '\u4e00' <= char <= '\u9fff' else 1
            if current_len + char_len > target_len:
                break
            current_len += char_len
            result += char
            
        return result + ".."
