from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.base_game_list_window import BaseGameListWindow

class AchievementWindow(BaseGameListWindow):
    request_fetch_achievements = pyqtSignal(list) # list of appids

    def __init__(self, parent=None):
        super().__init__("成就统计", parent)
        
        self.current_achievements = {} # {appid: {total: 10, unlocked: 5}}

        self.fetch_btn = QPushButton("获取当前标签页游戏成就统计")
        self.fetch_btn.clicked.connect(self.fetch_stats)
        self.toolbar_layout.addWidget(self.fetch_btn)
        self.toolbar_layout.addStretch()
        
        # 初始化空状态
        self.update_data([])

    def on_data_updated(self, **kwargs):
        self.current_achievements = kwargs.get("achievements", {})

    def on_tabs_refresh_start(self):
        self.fetch_btn.setEnabled(True)

    def show_empty_state(self):
        super().show_empty_state()
        self.fetch_btn.setEnabled(False)

    def setup_table(self, table):
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["游戏名称", "AppID", "总游玩时长", "成就进度", "完成率"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setSortingEnabled(True)

    def populate_tab(self, tab_info):
        entry = tab_info["entry"]
        data = entry.get("data") or {}
        games = data.get("all_games", [])
        achievements = self.current_achievements

        table = tab_info["table"]
        table.setRowCount(len(games))
        table.clearContents()

        total_achievements = 0
        unlocked_achievements = 0
        games_with_achievements = 0

        for row, game in enumerate(games):
            appid = game.get("appid")
            name = game.get("name", "Unknown")
            playtime_min = game.get("playtime_forever", 0)
            playtime_hour = round(playtime_min / 60, 1)

            ach_data = achievements.get(str(appid))
            ach_str = "未获取"
            percent_str = "-"
            percent_val = -1
            
            if ach_data:
                total = ach_data.get("total", 0)
                unlocked = ach_data.get("unlocked", 0)
                if total > 0:
                    ach_str = f"{unlocked}/{total}"
                    percent = (unlocked / total) * 100
                    percent_str = f"{percent:.1f}%"
                    percent_val = percent
                    
                    total_achievements += total
                    unlocked_achievements += unlocked
                    games_with_achievements += 1
                else:
                    ach_str = "无成就"
                    percent_str = "N/A"

            item_name = QTableWidgetItem(name)
            table.setItem(row, 0, item_name)

            item_id = QTableWidgetItem(str(appid))
            table.setItem(row, 1, item_id)

            item_time = QTableWidgetItem()
            item_time.setData(Qt.ItemDataRole.DisplayRole, playtime_hour)
            table.setItem(row, 2, item_time)

            item_ach = QTableWidgetItem(ach_str)
            table.setItem(row, 3, item_ach)
            
            item_percent = QTableWidgetItem()
            item_percent.setData(Qt.ItemDataRole.DisplayRole, percent_val)
            item_percent.setText(percent_str)
            table.setItem(row, 4, item_percent)

        stats_label = tab_info["stats_label"]
        stats_label.setText(
            f"共 {len(games)} 款游戏 | 已统计 {games_with_achievements} 款 | 总解锁成就: {unlocked_achievements}/{total_achievements}"
        )

    def fetch_stats(self):
        index = self.tabs.currentIndex()
        if index < 0 or index >= len(self.dataset_tabs):
            return

        tab_info = self.dataset_tabs[index]
        data = tab_info["entry"].get("data") or {}
        games = data.get("all_games", [])
        if not games:
            return

        # 筛选出玩过的游戏，且未获取成就数据的
        to_fetch = []
        limit = 50 # 限制每次获取的数量，避免 API 限制
        
        # 优先获取最近玩过的
        sorted_games = sorted(games, key=lambda x: x.get('rtime_last_played', 0), reverse=True)
        
        for game in sorted_games:
            appid = game.get("appid")
            if str(appid) not in self.current_achievements:
                to_fetch.append(appid)
                if len(to_fetch) >= limit:
                    break

        if to_fetch:
            tab_info["stats_label"].setText(f"正在获取 {len(to_fetch)} 款游戏的成就数据，请稍候...")
            self.request_fetch_achievements.emit(to_fetch)
        else:
            QMessageBox.information(self, "提示", "当前列表成就数据已获取。")
