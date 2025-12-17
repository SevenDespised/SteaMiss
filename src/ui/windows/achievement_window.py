from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHeaderView, QMessageBox, QPushButton, QTableWidgetItem

from src.ui.windows.base_game_list_window import BaseGameListWindow


class AchievementWindow(BaseGameListWindow):
    request_fetch_achievements = pyqtSignal(list)  # list of appids

    def __init__(self, parent=None):
        super().__init__("成就统计", parent)

        self.current_achievements = {}  # {appid: {total: 10, unlocked: 5}}

        self.fetch_btn = QPushButton("获取当前标签页游戏成就统计")
        self.fetch_btn.clicked.connect(self.fetch_stats)
        self.toolbar_layout.addWidget(self.fetch_btn)

        self.refetch_all_btn = QPushButton("重新获取所有成就")
        self.refetch_all_btn.setToolTip("强制重新获取当前标签页所有游戏的成就数据")
        self.refetch_all_btn.clicked.connect(self.refetch_all_achievements)
        self.toolbar_layout.addWidget(self.refetch_all_btn)

        self.toolbar_layout.addStretch()

        self.update_data([])

    def on_data_updated(self, **kwargs):
        self.current_achievements = kwargs.get("achievements", {})
        # 数据更新时恢复按钮状态
        self._restore_refetch_button()

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

    def _fetch_achievements_impl(self, force_refetch=False, show_button_feedback=False):
        """
        获取成就数据的通用实现

        Args:
            force_refetch: 是否强制重新获取所有数据（忽略缓存）
            show_button_feedback: 是否显示按钮状态反馈
        """
        index = self.tabs.currentIndex()
        if index < 0 or index >= len(self.dataset_tabs):
            return

        tab_info = self.dataset_tabs[index]
        data = tab_info["entry"].get("data") or {}
        games = data.get("all_games", [])
        if not games:
            if force_refetch:
                QMessageBox.information(self, "提示", "当前标签页没有游戏数据。")
            return

        # 获取需要拉取的游戏列表（按最近游玩时间排序）
        sorted_games = sorted(games, key=lambda x: x.get("rtime_last_played", 0), reverse=True)

        if force_refetch:
            # 强制刷新：获取所有游戏
            to_fetch_all = [game.get("appid") for game in sorted_games if game.get("appid")]
            if not to_fetch_all:
                QMessageBox.information(self, "提示", "当前标签页没有有效的游戏数据。")
                return
        else:
            # 普通获取：只获取未缓存的游戏
            to_fetch_all = [game.get("appid") for game in sorted_games
                          if game.get("appid") and str(game.get("appid")) not in self.current_achievements]
            if not to_fetch_all:
                QMessageBox.information(self, "提示", "当前列表成就数据已获取。")
                return

        total = len(to_fetch_all)
        limit = 50
        batches = (total + limit - 1) // limit

        # 更新UI状态
        operation_text = "重新获取" if force_refetch else "获取"
        tab_info["stats_label"].setText(f"将分 {batches} 批{operation_text}成就（每批≤{limit}），共 {total} 款，请稍候…")

        # 按钮状态管理（仅在强制刷新时）
        if show_button_feedback and force_refetch:
            self.refetch_all_btn.setEnabled(False)
            self.refetch_all_btn.setText("重新获取中...")

        # 分批发送请求
        for i in range(0, total, limit):
            chunk = to_fetch_all[i : i + limit]
            self.request_fetch_achievements.emit(chunk)

        # 超时恢复（仅在强制刷新时）
        if show_button_feedback and force_refetch:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(30000, lambda: self._restore_refetch_button())

    def fetch_stats(self):
        """获取当前标签页中未获取成就数据的游戏"""
        self._fetch_achievements_impl(force_refetch=False, show_button_feedback=False)

    def refetch_all_achievements(self):
        """强制重新获取当前标签页所有游戏的成就数据（忽略缓存）"""
        self._fetch_achievements_impl(force_refetch=True, show_button_feedback=True)

    def _restore_refetch_button(self):
        """恢复重新获取按钮的状态"""
        if hasattr(self, 'refetch_all_btn'):
            self.refetch_all_btn.setEnabled(True)
            self.refetch_all_btn.setText("重新获取所有成就")


__all__ = ["AchievementWindow"]


