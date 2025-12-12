from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QWidget,
    QTabWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal


class AllGamesWindow(QDialog):
    request_fetch_prices = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("所有游戏统计")
        self.resize(820, 620)

        self.dataset_tabs = []
        self.current_datasets = []
        self.current_prices = {}

        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        self.calc_price_btn = QPushButton("计算当前标签页未获取的游戏价格")
        self.calc_price_btn.clicked.connect(self.calculate_prices)
        btn_layout.addWidget(self.calc_price_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        
        # 初始化空状态
        self.update_data([], {})

    def update_data(self, datasets, prices):
        self.current_datasets = datasets
        self.current_prices = prices
        self.refresh_tabs()

    def refresh_tabs(self):
        self.tabs.clear()
        self.dataset_tabs = []

        if not self.current_datasets:
            placeholder = QWidget()
            ph_layout = QVBoxLayout()
            msg = QLabel("暂无数据，请先刷新 Steam 统计。")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ph_layout.addStretch()
            ph_layout.addWidget(msg)
            ph_layout.addStretch()
            placeholder.setLayout(ph_layout)
            self.tabs.addTab(placeholder, "总计")
            self.calc_price_btn.setEnabled(False)
            return

        self.calc_price_btn.setEnabled(True)

        for entry in self.current_datasets:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout()

            stats_label = QLabel("正在加载数据...")
            tab_layout.addWidget(stats_label)

            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["游戏名称", "AppID", "总游玩时长 (小时)", "当前价格 (CNY)"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            table.setSortingEnabled(True)
            tab_layout.addWidget(table)

            tab_widget.setLayout(tab_layout)
            self.tabs.addTab(tab_widget, entry["label"])

            tab_info = {
                "entry": entry,
                "widget": tab_widget,
                "stats_label": stats_label,
                "table": table,
            }
            self.dataset_tabs.append(tab_info)
            self.populate_tab(tab_info)

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

        prices = self.steam_manager.cache.get("prices", {})
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

    # update_prices 和 on_games_stats_updated 已被 update_data 替代，移除

