from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.base_game_list_window import BaseGameListWindow

class AllGamesWindow(BaseGameListWindow):
    request_fetch_prices = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__("所有游戏统计", parent)
        
        self.current_prices = {}

        self.calc_price_btn = QPushButton("计算当前标签页未获取的游戏价格")
        self.calc_price_btn.clicked.connect(self.calculate_prices)
        self.toolbar_layout.addWidget(self.calc_price_btn)
        self.toolbar_layout.addStretch()
        
        # 初始化空状态
        self.update_data([])

    def on_data_updated(self, **kwargs):
        self.current_prices = kwargs.get("prices", {})

    def on_tabs_refresh_start(self):
        self.calc_price_btn.setEnabled(True)

    def show_empty_state(self):
        super().show_empty_state()
        self.calc_price_btn.setEnabled(False)

    def setup_table(self, table):
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["游戏名称", "AppID", "总游玩时长 (小时)", "当前价格 (CNY)"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setSortingEnabled(True)

    def populate_tab(self, tab_info):
        entry = tab_info["entry"]
        data = entry.get("data") or {}
        games = data.get("all_games", [])
        prices = self.current_prices

        table = tab_info["table"]
        table.setRowCount(len(games))
        table.clearContents()

        total_playtime = 0
        total_price = 0
        price_count = 0

        for row, game in enumerate(games):
            appid = game.get("appid")
            name = game.get("name", "Unknown")
            playtime_min = game.get("playtime_forever", 0)
            playtime_hour = round(playtime_min / 60, 1)

            total_playtime += playtime_min

            price_str = "未获取"
            price_val = 0
            price_entry = prices.get(str(appid))
            if price_entry and price_entry.get("success"):
                data_block = price_entry.get("data", {})
                if isinstance(data_block, dict):
                    if data_block.get("is_free"):
                        price_str = "免费"
                    elif "price_overview" in data_block:
                        price_val = data_block["price_overview"].get("final", 0) / 100
                        price_str = f"¥{price_val:.2f}"
                        total_price += price_val
                        price_count += 1

            item_name = QTableWidgetItem(name)
            table.setItem(row, 0, item_name)

            item_id = QTableWidgetItem(str(appid))
            table.setItem(row, 1, item_id)

            item_time = QTableWidgetItem()
            item_time.setData(Qt.ItemDataRole.DisplayRole, playtime_hour)
            table.setItem(row, 2, item_time)

            item_price = QTableWidgetItem(price_str)
            if price_str not in ("未获取", "免费"):
                item_price.setData(Qt.ItemDataRole.UserRole, price_val)
            table.setItem(row, 3, item_price)

        stats_label = tab_info["stats_label"]
        stats_label.setText(
            f"共 {len(games)} 款游戏 | 总时长: {int(total_playtime/60)} 小时 | 已统计 {price_count} 款游戏价值: ¥{total_price:.2f}"
        )

    def calculate_prices(self):
        index = self.tabs.currentIndex()
        if index < 0 or index >= len(self.dataset_tabs):
            return

        tab_info = self.dataset_tabs[index]
        data = tab_info["entry"].get("data") or {}
        games = data.get("all_games", [])
        if not games:
            tab_info["stats_label"].setText("当前标签页没有可统计的游戏。")
            return

        # 注意：这里不再直接访问 steam_manager，而是依赖 current_prices
        # 但 calculate_prices 需要知道哪些价格缺失。
        # current_prices 应该包含所有已知的价格。
        
        prices = self.current_prices
        to_fetch = []
        limit = 50
        for game in games:
            appid = game.get("appid")
            if str(appid) not in prices:
                to_fetch.append(appid)
                if len(to_fetch) >= limit:
                    break

        if to_fetch:
            tab_info["stats_label"].setText(f"正在获取 {len(to_fetch)} 款游戏的价格，请稍候...")
            self.request_fetch_prices.emit(to_fetch)
        else:
            tab_info["stats_label"].setText("所有游戏价格已获取或已达到本标签页的限制。")


