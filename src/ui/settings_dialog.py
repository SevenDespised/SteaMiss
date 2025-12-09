from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTabWidget, QWidget, QHBoxLayout, QListWidget, QGroupBox, QFormLayout
from PyQt6.QtCore import Qt
from src.ui.all_games_window import AllGamesWindow
import datetime

class SettingsDialog(QDialog):
    def __init__(self, config_manager, steam_manager=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.steam_manager = steam_manager # 传入 SteamManager 以支持搜索
        self.setWindowTitle("功能设置")
        self.resize(500, 600) # 稍微调大一点
        
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # Tab 1: 打招呼
        self.hello_tab = QWidget()
        self.init_hello_tab()
        self.tabs.addTab(self.hello_tab, "打招呼")
        
        # Tab 2: 功能设置
        self.func_tab = QWidget()
        self.init_func_tab()
        self.tabs.addTab(self.func_tab, "功能")

        # Tab 3: Steam 设置
        self.steam_tab = QWidget()
        self.init_steam_tab()
        self.tabs.addTab(self.steam_tab, "Steam")

        # Tab 4: 游玩记录 (Stats)
        self.stats_tab = QWidget()
        self.init_stats_tab()
        self.tabs.addTab(self.stats_tab, "游玩记录")
        
        # Tab 5: 闹钟 (Empty)
        self.tabs.addTab(QWidget(), "闹钟")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # 连接信号以更新统计界面
        if self.steam_manager:
            self.steam_manager.on_player_summary.connect(self.update_stats_ui)
            self.steam_manager.on_games_stats.connect(self.update_stats_ui)

    def init_stats_tab(self):
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
        self.btn_all_games = QPushButton("查看所有库存游戏 & 价值统计")
        self.btn_all_games.clicked.connect(self.open_all_games_window)
        layout.addWidget(self.btn_all_games)
        
        layout.addStretch()
        self.stats_tab.setLayout(layout)
        
        # 尝试初始化显示
        self.update_stats_ui()

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
        win = AllGamesWindow(self.steam_manager, self)
        win.show()

    def init_hello_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("自定义打招呼内容:"))
        self.hello_input = QLineEdit()
        self.hello_input.setText(self.config_manager.get("say_hello_content", "你好！"))
        layout.addWidget(self.hello_input)
        layout.addStretch()
        self.hello_tab.setLayout(layout)

    def init_func_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("默认打开路径:"))
        self.path_input = QLineEdit()
        self.path_input.setText(self.config_manager.get("explorer_path", "C:/"))
        layout.addWidget(self.path_input)
        layout.addStretch()
        self.func_tab.setLayout(layout)

    def init_steam_tab(self):
        layout = QVBoxLayout()
        
        # Steam ID
        layout.addWidget(QLabel("Steam ID (64位):"))
        self.steam_id_input = QLineEdit()
        self.steam_id_input.setPlaceholderText("例如: 76561198000000000")
        self.steam_id_input.setText(self.config_manager.get("steam_id", ""))
        layout.addWidget(self.steam_id_input)
        
        # API Key
        layout.addWidget(QLabel("Steam Web API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("在此输入你的 API Key")
        # 设置为密码模式，进行脱敏显示
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(self.config_manager.get("steam_api_key", ""))
        layout.addWidget(self.api_key_input)
        
        layout.addSpacing(10)
        layout.addWidget(QLabel("--- 常用游戏设置 ---"))
        
        # 当前最爱
        fav_game = self.config_manager.get("steam_favorite_game", {})
        fav_name = fav_game.get("name", "未设置")
        self.fav_label = QLabel(f"当前最爱: {fav_name}")
        layout.addWidget(self.fav_label)
        
        # 搜索区域
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索游戏名...")
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.search_games)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        # 结果列表
        self.game_list = QListWidget()
        self.game_list.itemClicked.connect(self.on_game_selected)
        layout.addWidget(self.game_list)
        
        # 临时存储选中的游戏
        self.selected_game = None
        
        layout.addStretch()
        self.steam_tab.setLayout(layout)

    def search_games(self):
        if not self.steam_manager:
            self.game_list.clear()
            self.game_list.addItem("错误: Steam服务未连接")
            return
            
        keyword = self.search_input.text()
        if not keyword:
            return
            
        # 尝试搜索
        results = self.steam_manager.search_games(keyword)
        self.game_list.clear()
        
        if not results:
            # 如果没搜到，可能是还没拉取过数据，尝试拉取一次
            # 注意：这里是异步的，所以第一次可能搜不到，需要提示用户稍后再试
            # 或者在这里触发 fetch，并提示用户
            self.game_list.addItem("正在更新游戏库，请稍候...")
            
            # 连接信号以在数据准备好后自动刷新
            # 先断开可能的旧连接以防重复
            try:
                self.steam_manager.on_games_stats.disconnect(self.refresh_search_results)
            except TypeError:
                pass # 如果没有连接过，disconnect 会抛出异常，忽略即可
                
            self.steam_manager.on_games_stats.connect(self.refresh_search_results)
            self.steam_manager.fetch_games_stats()
            return
            
        for game in results:
            name = game.get("name", "Unknown")
            appid = game.get("appid")
            self.game_list.addItem(f"{name} | {appid}")

    def refresh_search_results(self, data):
        """当 Steam 数据更新完成后，自动重新执行搜索"""
        # 断开信号，避免后续不必要的刷新
        try:
            self.steam_manager.on_games_stats.disconnect(self.refresh_search_results)
        except TypeError:
            pass
            
        # 重新执行搜索
        self.search_games()

    def on_game_selected(self, item):
        text = item.text()
        if "|" in text:
            name, appid = text.split(" | ")
            self.selected_game = {"name": name.strip(), "appid": int(appid)}
            self.fav_label.setText(f"当前选中: {name}")

    def save_settings(self):
        # Save Hello Content
        text = self.hello_input.text()
        self.config_manager.set("say_hello_content", text)
        
        # Save Explorer Path
        path = self.path_input.text()
        self.config_manager.set("explorer_path", path)
        
        # Save Steam Config
        self.config_manager.set("steam_id", self.steam_id_input.text())
        self.config_manager.set("steam_api_key", self.api_key_input.text())
        
        # Save Favorite Game
        if self.selected_game:
            self.config_manager.set("steam_favorite_game", self.selected_game)
        
        self.accept()
