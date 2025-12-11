from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, 
                             QListWidgetItem, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, QSize, QUrl
from PyQt6.QtGui import QDesktopServices

class DiscountItemWidget(QWidget):
    def __init__(self, game_data, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 1. 游戏名称
        name_label = QLabel(game_data['name'])
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label, 1) # Stretch factor 1
        
        # 2. 折扣信息
        discount_label = QLabel(f"-{game_data['discount_pct']}%")
        discount_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px; background-color: #4c6b22; padding: 4px; border-radius: 4px;")
        discount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        discount_label.setFixedWidth(60)
        layout.addWidget(discount_label)
        
        # 3. 价格
        price_label = QLabel(game_data['price'])
        price_label.setStyleSheet("color: #333; font-weight: bold;")
        price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price_label.setFixedWidth(80)
        layout.addWidget(price_label)
        
        # 4. 商店链接按钮
        btn = QPushButton("查看")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedWidth(60)
        btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"https://store.steampowered.com/app/{game_data['appid']}")))
        layout.addWidget(btn)
        
        self.setLayout(layout)

class DiscountWindow(QWidget):
    def __init__(self, steam_manager):
        super().__init__()
        self.steam_manager = steam_manager
        self.setWindowTitle("愿望单/关注游戏特惠推荐")
        self.resize(550, 600)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("愿望单/关注游戏中的打折游戏 (Top 10)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet("QListWidget::item { border-bottom: 1px solid #eee; }")
        layout.addWidget(self.list_widget)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新数据")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setMinimumHeight(40)
        layout.addWidget(self.refresh_btn)
        
        self.setLayout(layout)
        
        # 连接信号
        if self.steam_manager:
            self.steam_manager.on_wishlist_data.connect(self.update_list)
            
        # 初始加载
        # 如果缓存有数据则显示
        if self.steam_manager and "wishlist" in self.steam_manager.cache:
            self.update_list(self.steam_manager.cache["wishlist"])
        else:
            self.refresh_data()

    def refresh_data(self):
        if not self.steam_manager: return
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("正在获取愿望单数据...")
        self.steam_manager.fetch_wishlist()
        
        # 简单的超时恢复
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(8000, lambda: self.refresh_btn.setEnabled(True))
        QTimer.singleShot(8000, lambda: self.refresh_btn.setText("刷新数据"))

    def update_list(self, games):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新数据")
        self.list_widget.clear()
        
        if not games:
            item = QListWidgetItem("暂无打折推荐或数据加载失败")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_widget.addItem(item)
            return
            
        for game in games:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 70))
            
            widget = DiscountItemWidget(game)
            self.list_widget.setItemWidget(item, widget)
