from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QFormLayout,
    QListWidget,
    QPushButton,
    QHBoxLayout,
    QTabWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
import datetime

class StatsWindow(QWidget):
    # 定义信号
    request_refresh = pyqtSignal()
    request_open_all_games = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("游玩记录")
        self.resize(500, 600)
        
        layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 4. 按钮
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("刷新数据")
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        btn_layout.addWidget(self.btn_refresh)
        
        self.btn_all_games = QPushButton("查看所有库存游戏 & 价值统计")
        self.btn_all_games.clicked.connect(self.request_open_all_games.emit)
        btn_layout.addWidget(self.btn_all_games)
        
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # 初始化显示空状态
        self.update_data([], {}, {})

    def _on_refresh_clicked(self):
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("刷新中...")
        self.request_refresh.emit()
        
        # 简单的 UI 恢复逻辑，实际应该由外部控制或通过回调
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.btn_refresh.setEnabled(True))
        QTimer.singleShot(3000, lambda: self.btn_refresh.setText("刷新数据"))

    def update_data(self, datasets, fallback_summary, config):
        """
        更新 UI 数据
        :param datasets: 游戏数据集列表
        :param fallback_summary: 默认的玩家信息摘要
        :param config: 配置信息 (用于获取 steam_id)
        """
        self.tabs.clear()

        if not datasets:
            empty_tab = self._build_empty_tab()
            self.tabs.addTab(empty_tab, "总计")
            return

        for entry in datasets:
            summary_obj = entry.get("summary")
            if summary_obj is None and entry.get("key") == "primary":
                summary_obj = fallback_summary

            if entry.get("key") == "total" and summary_obj is None:
                summary_obj = fallback_summary

            include_summary = entry.get("key") != "total" or summary_obj is not None
            steam_id_value = entry.get("steam_id")
            if steam_id_value is None and entry.get("key") == "total":
                steam_id_value = config.get("steam_id")
            tab_info = self._build_stats_tab(include_summary)
            self._apply_dataset_to_tab(
                tab_info,
                entry.get("data", {}),
                summary_obj,
                steam_id_value,
            )
            self.tabs.addTab(tab_info["widget"], entry["label"])

    def _build_stats_tab(self, include_summary):
        tab = QWidget()
        layout = QVBoxLayout()

        summary_refs = None
        if include_summary:
            info_group = QGroupBox("个人信息")
            info_layout = QFormLayout()
            lbl_name = QLabel("加载中...")
            lbl_level = QLabel("Lv. ?")
            lbl_created = QLabel("?")
            lbl_sid = QLabel("-")
            info_layout.addRow("昵称:", lbl_name)
            info_layout.addRow("等级:", lbl_level)
            info_layout.addRow("注册时间:", lbl_created)
            info_layout.addRow("Steam ID:", lbl_sid)
            info_group.setLayout(info_layout)
            layout.addWidget(info_group)
            summary_refs = {
                "name": lbl_name,
                "level": lbl_level,
                "created": lbl_created,
                "steam_id": lbl_sid,
            }

        stats_group = QGroupBox("库统计")
        stats_layout = QFormLayout()
        lbl_game_count = QLabel("0")
        lbl_total_time = QLabel("0 小时")
        stats_layout.addRow("游戏总数:", lbl_game_count)
        stats_layout.addRow("总游玩时长:", lbl_total_time)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addWidget(QLabel("最近两周游玩 (Top 5):"))
        recent_list = QListWidget()
        recent_list.setMaximumHeight(120)
        layout.addWidget(recent_list)

        layout.addStretch()
        tab.setLayout(layout)

        return {
            "widget": tab,
            "summary": summary_refs,
            "stats": {
                "game_count": lbl_game_count,
                "total_time": lbl_total_time,
            },
            "recent_list": recent_list,
        }

    def _apply_dataset_to_tab(self, tab_info, data, summary, steam_id):
        stats_refs = tab_info["stats"]
        stats_refs["game_count"].setText(str(data.get("count", 0)))

        total_min = data.get("total_playtime", 0)
        total_hours = int(total_min / 60)
        stats_refs["total_time"].setText(f"{total_hours} 小时")

        recent_list = tab_info["recent_list"]
        recent_list.clear()
        for game in data.get("top_2weeks", [])[:5]:
            name = game.get("name", "Unknown")
            mins = game.get("playtime_2weeks", 0)
            recent_list.addItem(f"{name} - {round(mins/60, 1)} 小时")

        if tab_info["summary"] is not None:
            ref = tab_info["summary"]
            if summary:
                ref["name"].setText(summary.get("personaname", "Unknown"))
                ref["level"].setText(f"Lv. {summary.get('steam_level', '?')}")
                ts = summary.get("timecreated", 0)
                if ts:
                    dt = datetime.datetime.fromtimestamp(ts)
                    ref["created"].setText(dt.strftime("%Y-%m-%d"))
                else:
                    ref["created"].setText("?")
                sid_text = summary.get("steamid") or steam_id or "-"
                ref["steam_id"].setText(sid_text)
            else:
                ref["name"].setText("未获取")
                ref["level"].setText("Lv. ?")
                ref["created"].setText("?")
                ref["steam_id"].setText(steam_id or "未填写")

    def _build_empty_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addStretch()
        msg = QLabel("暂无数据，请先填写主账号后刷新。")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        layout.addStretch()
        tab.setLayout(layout)
        return tab
