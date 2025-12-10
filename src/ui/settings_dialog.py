from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTabWidget, QWidget, QHBoxLayout, QListWidget

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

        # Tab 4: 闹钟 (Empty)
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
        
        # 路径设置
        layout.addWidget(QLabel("--- 快捷路径设置 ---"))
        
        # 读取配置，默认为3个C:/
        paths = self.config_manager.get("explorer_paths", ["C:/", "C:/", "C:/"])
        aliases = self.config_manager.get("explorer_path_aliases", ["", "", ""])
        
        # 确保 aliases 长度足够
        while len(aliases) < 3:
            aliases.append("")
            
        self.path_inputs = []
        self.alias_inputs = []
        labels = ["主路径 (Top 1)", "副路径 1 (Top 2)", "副路径 2 (Top 3)"]
        
        for i in range(3):
            layout.addWidget(QLabel(f"{labels[i]}:"))
            
            row_layout = QHBoxLayout()
            
            path_inp = QLineEdit()
            path_inp.setPlaceholderText("路径 (例如 C:/)")
            path_inp.setText(paths[i])
            self.path_inputs.append(path_inp)
            
            alias_inp = QLineEdit()
            alias_inp.setPlaceholderText("显示名称 (可选)")
            alias_inp.setText(aliases[i])
            self.alias_inputs.append(alias_inp)
            
            row_layout.addWidget(path_inp, 2)
            row_layout.addWidget(alias_inp, 1)
            
            layout.addLayout(row_layout)
            
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
        layout.addWidget(QLabel("--- 快速启动设置 (最多3个) ---"))
        
        # 初始化数据
        self.quick_launch_games = self.config_manager.get("steam_quick_launch_games", [None, None, None])
        # 兼容旧配置：如果列表全空，且有旧的 favorite，则填入第一个
        if not isinstance(self.quick_launch_games, list):
            self.quick_launch_games = [None, None, None]

        # 确保长度为3
        while len(self.quick_launch_games) < 3:
            self.quick_launch_games.append(None)
            
        # 显示当前配置的3个槽位
        self.slot_labels = []
        for i in range(3):
            game = self.quick_launch_games[i]
            name = game.get("name", "未设置") if game else f"默认 (Top {i+1})"
            lbl = QLabel(f"槽位{i+1}: {name}")
            self.slot_labels.append(lbl)
            layout.addWidget(lbl)
        
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
        
        # 分配按钮
        assign_layout = QHBoxLayout()
        for i in range(3):
            btn = QPushButton(f"设为槽位 {i+1}")
            btn.clicked.connect(lambda checked, idx=i: self.assign_to_slot(idx))
            assign_layout.addWidget(btn)
            
        # 清除按钮
        clear_btn = QPushButton("清除槽位")
        clear_btn.clicked.connect(self.clear_slot_dialog) # 弹出对话框或简单清除
        assign_layout.addWidget(clear_btn)
        
        layout.addLayout(assign_layout)
        
        # 临时存储选中的游戏
        self.selected_game = None
        
        layout.addStretch()
        self.steam_tab.setLayout(layout)

    def assign_to_slot(self, idx):
        if not self.selected_game:
            return
        self.quick_launch_games[idx] = self.selected_game
        self.slot_labels[idx].setText(f"槽位{idx+1}: {self.selected_game['name']}")

    def clear_slot_dialog(self):
        # 简单实现：清除所有，或者清除最后一个？
        # 这里为了简单，清除当前选中的槽位？不，没有选中槽位的概念。
        # 让我们做一个简单的清除：清除所有配置，恢复默认
        for i in range(3):
            self.quick_launch_games[i] = None
            self.slot_labels[i].setText(f"槽位{i+1}: 默认 (Top {i+1})")

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
            # self.fav_label.setText(f"当前选中: {name}") # 移除旧标签引用

    def save_settings(self):
        # Save Hello Content
        text = self.hello_input.text()
        self.config_manager.set("say_hello_content", text)
        
        # Save Explorer Paths
        paths = [inp.text() for inp in self.path_inputs]
        self.config_manager.set("explorer_paths", paths)
        
        aliases = [inp.text() for inp in self.alias_inputs]
        self.config_manager.set("explorer_path_aliases", aliases)
        
        # Save Steam Config
        self.config_manager.set("steam_id", self.steam_id_input.text())
        self.config_manager.set("steam_api_key", self.api_key_input.text())
        
        # Save Quick Launch Games
        self.config_manager.set("steam_quick_launch_games", self.quick_launch_games)
        
        self.accept()
