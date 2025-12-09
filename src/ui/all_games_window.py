from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class AllGamesWindow(QDialog):
    def __init__(self, steam_manager, parent=None):
        super().__init__(parent)
        self.steam_manager = steam_manager
        self.setWindowTitle("所有游戏统计")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # 顶部统计
        self.stats_label = QLabel("正在加载数据...")
        layout.addWidget(self.stats_label)
        
        # 按钮区
        btn_layout = QHBoxLayout()
        self.calc_price_btn = QPushButton("计算选中/所有游戏价值 (可能较慢)")
        self.calc_price_btn.clicked.connect(self.calculate_prices)
        btn_layout.addWidget(self.calc_price_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["游戏名称", "AppID", "总游玩时长 (小时)", "当前价格 (CNY)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        # 连接信号
        self.steam_manager.on_store_prices.connect(self.update_prices)
        
        # 初始化数据
        self.load_data()

    def load_data(self):
        if "games" not in self.steam_manager.cache:
            return
            
        games = self.steam_manager.cache["games"].get("all_games", [])
        prices = self.steam_manager.cache.get("prices", {})
        
        self.table.setRowCount(len(games))
        
        total_playtime = 0
        total_price = 0
        price_count = 0
        
        for row, game in enumerate(games):
            appid = game.get("appid")
            name = game.get("name", "Unknown")
            playtime_min = game.get("playtime_forever", 0)
            playtime_hour = round(playtime_min / 60, 1)
            
            total_playtime += playtime_min
            
            # 价格处理
            price_str = "未获取"
            price_val = 0
            if str(appid) in prices:
                p_data = prices[str(appid)]
                if p_data.get("success"):
                    data = p_data.get("data", {})
                    if data.get("is_free"):
                        price_str = "免费"
                    elif "price_overview" in data:
                        price_val = data["price_overview"].get("final", 0) / 100
                        price_str = f"¥{price_val:.2f}"
                        total_price += price_val
                        price_count += 1
            
            # 设置单元格
            # Name
            item_name = QTableWidgetItem(name)
            self.table.setItem(row, 0, item_name)
            
            # AppID
            item_id = QTableWidgetItem(str(appid))
            self.table.setItem(row, 1, item_id)
            
            # Playtime (使用自定义 Item 以支持数字排序)
            item_time = QTableWidgetItem()
            item_time.setData(Qt.ItemDataRole.DisplayRole, playtime_hour)
            self.table.setItem(row, 2, item_time)
            
            # Price
            item_price = QTableWidgetItem(price_str)
            if price_str != "未获取" and price_str != "免费":
                 item_price.setData(Qt.ItemDataRole.UserRole, price_val) # 用于排序
            self.table.setItem(row, 3, item_price)

        # 更新顶部统计
        self.stats_label.setText(f"共 {len(games)} 款游戏 | 总时长: {int(total_playtime/60)} 小时 | 已统计 {price_count} 款游戏价值: ¥{total_price:.2f}")

    def calculate_prices(self):
        """触发价格计算"""
        if "games" not in self.steam_manager.cache:
            return
            
        games = self.steam_manager.cache["games"].get("all_games", [])
        # 找出还没有价格的 appid
        prices = self.steam_manager.cache.get("prices", {})
        to_fetch = []
        
        # 限制一次获取的数量，防止太久
        limit = 50 
        for game in games:
            if str(game.get("appid")) not in prices:
                to_fetch.append(game.get("appid"))
                if len(to_fetch) >= limit:
                    break
        
        if to_fetch:
            self.stats_label.setText(f"正在获取 {len(to_fetch)} 款游戏的价格，请稍候...")
            self.steam_manager.fetch_store_prices(to_fetch)
        else:
            self.stats_label.setText("所有游戏价格已获取 (或已达到单次限制)")

    def update_prices(self, data):
        self.load_data()
