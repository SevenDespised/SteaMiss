from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QListWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from src.ui.all_games_window import AllGamesWindow
import datetime

class StatsWindow(QWidget):
    def __init__(self, steam_manager):
        super().__init__()
        self.steam_manager = steam_manager
        self.setWindowTitle("游玩记录")
        self.resize(500, 600)
        
        layout = QVBoxLayout()
        
        # 1. 个人信息区域
        self.info_group = QGroupBox("个人信息")
        info_layout = QFormLayout()
        self.lbl_name = QLabel("加载中...")
        self.lbl_level = QLabel("Lv. ?")
        self.lbl_created = QLabel("?")
        info_layout.addRow("昵称:", self.lbl_name)
        info_layout.addRow("等级:", self.lbl_level)
        info_layout.addRow("注册时间:", self.lbl_created)
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        # 2. 统计概览
        self.stats_group = QGroupBox("库统计")
        stats_layout = QFormLayout()
        self.lbl_game_count = QLabel("0")
        self.lbl_total_time = QLabel("0 小时")
        stats_layout.addRow("游戏总数:", self.lbl_game_count)
        stats_layout.addRow("总游玩时长:", self.lbl_total_time)
        self.stats_group.setLayout(stats_layout)
        layout.addWidget(self.stats_group)
        
        # 3. 最近两周游玩 (Top 5)
        layout.addWidget(QLabel("最近两周游玩 (Top 5):"))
        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(120)
        layout.addWidget(self.recent_list)
        
        # 4. 按钮
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("刷新数据")
        self.btn_refresh.clicked.connect(self.refresh_stats)
        btn_layout.addWidget(self.btn_refresh)
        
        self.btn_all_games = QPushButton("查看所有库存游戏 & 价值统计")
        self.btn_all_games.clicked.connect(self.open_all_games_window)
        btn_layout.addWidget(self.btn_all_games)
        
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # 连接信号
        if self.steam_manager:
            self.steam_manager.on_player_summary.connect(self.update_stats_ui)
            self.steam_manager.on_games_stats.connect(self.update_stats_ui)
            
        # 初始化显示
        self.update_stats_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_stats_ui()

    def refresh_stats(self):
        """手动刷新统计数据"""
        if not self.steam_manager: return
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("刷新中...")
        self.steam_manager.fetch_player_summary()
        self.steam_manager.fetch_games_stats()
        
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.btn_refresh.setEnabled(True))
        QTimer.singleShot(3000, lambda: self.btn_refresh.setText("刷新数据"))

    def update_stats_ui(self):
        if not self.steam_manager: return
        
        # 更新个人信息
        if "summary" in self.steam_manager.cache:
            data = self.steam_manager.cache["summary"]
            self.lbl_name.setText(data.get("personaname", "Unknown"))
            self.lbl_level.setText(f"Lv. {data.get('steam_level', '?')}")
            
            ts = data.get("timecreated", 0)
            if ts:
                dt = datetime.datetime.fromtimestamp(ts)
                self.lbl_created.setText(dt.strftime("%Y-%m-%d"))
        
        # 更新游戏统计
        if "games" in self.steam_manager.cache:
            data = self.steam_manager.cache["games"]
            self.lbl_game_count.setText(str(data.get("count", 0)))
            
            total_min = data.get("total_playtime", 0)
            self.lbl_total_time.setText(f"{int(total_min/60)} 小时")
            
            # 更新最近列表
            self.recent_list.clear()
            top_2weeks = data.get("top_2weeks", [])
            for game in top_2weeks:
                name = game.get("name", "Unknown")
                mins = game.get("playtime_2weeks", 0)
                self.recent_list.addItem(f"{name} - {round(mins/60, 1)} 小时")

    def open_all_games_window(self):
        if not self.steam_manager: return
        # 注意：这里 AllGamesWindow 是 QDialog，如果 StatsWindow 是 QWidget，
        # 我们可能希望它是非模态的，或者模态的。
        # 这里保持原样，作为独立窗口打开
        self.all_games_win = AllGamesWindow(self.steam_manager)
        self.all_games_win.show()
