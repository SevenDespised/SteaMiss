import os
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from src.utils.path_utils import resource_path

class ResourceManager:
    def __init__(self):
        # 存储结构: { "idle": [QPixmap, QPixmap...], "point": [QPixmap...] }
        self.animations = {}
        self.default_image = None
        
        # 预加载所有资源
        self._load_all_resources()

    def _load_all_resources(self):
        """加载并缓存所有图片资源"""
        # 1. 加载默认图片
        self.default_image = self._load_processed_image(resource_path("assets", "main.png"))
        
        # 2. 加载交互图片 (用于环形菜单悬停)
        # 假设 point0.png 到 point7.png 代表8个方向
        self.animations["point"] = []
        for i in range(8):  # 假设有8个方向
            img = self._load_processed_image(resource_path("assets", f"point{i}.png"))
            # 如果某个方向没图，可以用默认图顶替，或者留空
            if img:
                self.animations["point"].append(img)
            else:
                # 如果对应图片不存在，回退到默认图片
                self.animations["point"].append(self.default_image)

        # 3. 加载其他状态 (idle, walk...)
        # self._load_animation_group("idle", resource_path("assets", "idle"))

    def _load_animation_group(self, state_name, folder_path):
        """加载一个文件夹下的所有序列帧"""
        if not os.path.exists(folder_path):
            return
            
        frames = []
        # 简单的按文件名排序加载
        files = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
        for f in files:
            img = self._load_processed_image(os.path.join(folder_path, f))
            if img:
                frames.append(img)
        
        if frames:
            self.animations[state_name] = frames

    def _load_processed_image(self, path):
        """加载单张图片并进行预处理（如缩放）"""
        path = str(path)
        if not os.path.exists(path):
            return None
            
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return None
            
        # 预处理：统一缩放到高质量尺寸，避免渲染时实时缩放
        # 这里设定一个最大宽度，防止图片过大
        if pixmap.width() > 500:
            pixmap = pixmap.scaled(
                500, 500,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        return pixmap

    def get_frame(self, state, frame_index=0):
        """
        核心接口：获取当前应该显示的图片
        """
        # 特殊处理：如果状态是 point (悬停)，frame_index 代表方向索引
        if state == "point":
            frames = self.animations.get("point", [])
            if frames and 0 <= frame_index < len(frames):
                return frames[frame_index]
            return self.default_image

        # 普通动画状态
        frames = self.animations.get(state)
        
        if not frames:
            return self.default_image
            
        # 安全取帧 (防止索引越界，实现循环播放)
        idx = frame_index % len(frames)
        return frames[idx]
