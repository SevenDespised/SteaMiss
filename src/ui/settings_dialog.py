from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QMessageBox,
    QComboBox,
)

class SettingsDialog(QDialog):
    def __init__(self, config_manager, steam_manager=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.steam_manager = steam_manager # 传入 SteamManager 以支持搜索
        self.setWindowTitle("功能设置")
        self.resize(500, 600) # 稍微调大一点
        
        # 动态存储控件引用
        self.alt_id_inputs = []
        
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Tab 1: Steam 设置
        self.steam_tab = QWidget()
        self.init_steam_tab()
        self.tabs.addTab(self.steam_tab, "Steam设置")
        
        # Tab 2: 打招呼
        self.hello_tab = QWidget()
        self.init_hello_tab()
        self.tabs.addTab(self.hello_tab, "打招呼")
        
        # Tab 3: 快捷路径
        self.func_tab = QWidget()
        self.init_func_tab()
        self.tabs.addTab(self.func_tab, "快捷路径")

        # Tab 4: 快速启动
        self.quick_tab = QWidget()
        self.init_quick_tab()
        self.tabs.addTab(self.quick_tab, "快速启动")

        # Tab 5: Steam页面
        self.steam_page_tab = QWidget()
        self.init_steam_page_tab()
        self.tabs.addTab(self.steam_page_tab, "Steam页面")

        # Tab 6: 闹钟 (Empty) (已移除，后续会变更为计时器相关)
        # self.tabs.addTab(QWidget(), "闹钟")
        
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
        
        # 主号 Steam ID
        layout.addWidget(QLabel("主账号 Steam ID (64位):"))
        self.steam_id_input = QLineEdit()
        self.steam_id_input.setPlaceholderText("例如: 76561198000000000")
        self.steam_id_input.setText(self.config_manager.get("steam_id", ""))
        self.steam_id_input.textChanged.connect(self.on_primary_id_changed)
        layout.addWidget(self.steam_id_input)
        
        # 小号 Steam ID 列表
        layout.addSpacing(6)
        layout.addWidget(QLabel("小号 Steam ID (最多3个):"))
        alt_header = QHBoxLayout()
        self.add_alt_btn = QPushButton("添加小号")
        self.add_alt_btn.clicked.connect(lambda: self.add_alt_id_input())
        alt_header.addWidget(self.add_alt_btn)
        alt_header.addStretch()
        layout.addLayout(alt_header)

        self.alt_id_container = QVBoxLayout()
        layout.addLayout(self.alt_id_container)

        alt_ids = self.config_manager.get("steam_alt_ids", [])
        if not isinstance(alt_ids, list):
            alt_ids = []

        if self.steam_id_input.text().strip():
            for sid in alt_ids[:3]:
                self.add_alt_id_input(sid)

        self._update_alt_add_btn_state()

        # API Key
        layout.addSpacing(10)
        layout.addWidget(QLabel("Steam Web API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("在此输入你的 API Key")
        # 设置为密码模式，进行脱敏显示
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(self.config_manager.get("steam_api_key", ""))
        layout.addWidget(self.api_key_input)
        
        layout.addStretch()
        self.steam_tab.setLayout(layout)

    def add_alt_id_input(self, value=""):
        """添加一个小号输入行"""
        if not self.steam_id_input.text().strip():
            QMessageBox.warning(self, "提示", "请先填写主账号 Steam ID，再添加小号。")
            self._update_alt_add_btn_state()
            return

        if len(self.alt_id_inputs) >= 3:
            return

        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)

        line = QLineEdit()
        line.setPlaceholderText("例如: 76561198...")
        line.setText(value)
        remove_btn = QPushButton("删除")
        remove_btn.clicked.connect(lambda: self.remove_alt_id_input(row_widget, line))

        row_layout.addWidget(line)
        row_layout.addWidget(remove_btn)
        row_widget.setLayout(row_layout)

        self.alt_id_container.addWidget(row_widget)
        self.alt_id_inputs.append(line)
        self._update_alt_add_btn_state()

    def remove_alt_id_input(self, row_widget, line_edit):
        """移除指定的小号输入行"""
        if line_edit in self.alt_id_inputs:
            self.alt_id_inputs.remove(line_edit)

        # 从布局中移除并销毁控件
        self.alt_id_container.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()
        self._update_alt_add_btn_state()

    def _update_alt_add_btn_state(self):
        if hasattr(self, "add_alt_btn"):
            has_primary = bool(self.steam_id_input.text().strip()) if hasattr(self, "steam_id_input") else False
            self.add_alt_btn.setEnabled(has_primary and len(self.alt_id_inputs) < 3)

    def on_primary_id_changed(self, text: str):
        text = text.strip()
        if not text and self.alt_id_inputs:
            self.clear_all_alt_inputs()
        self._update_alt_add_btn_state()

    def clear_all_alt_inputs(self):
        while self.alt_id_inputs:
            line = self.alt_id_inputs.pop()
            parent_widget = line.parentWidget()
            if parent_widget:
                self.alt_id_container.removeWidget(parent_widget)
                parent_widget.setParent(None)
                parent_widget.deleteLater()
        self._update_alt_add_btn_state()

    def init_quick_tab(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("--- 快速启动设置 (最多3个) ---"))

        # 初始化数据
        self.quick_launch_games = self.config_manager.get("steam_quick_launch_games", [None, None, None])
        if not isinstance(self.quick_launch_games, list):
            self.quick_launch_games = [None, None, None]

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
        clear_btn.clicked.connect(self.clear_slot_dialog)
        assign_layout.addWidget(clear_btn)
        
        layout.addLayout(assign_layout)
        
        # 临时存储选中的游戏
        self.selected_game = None
        
        layout.addStretch()
        self.quick_tab.setLayout(layout)

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

    def init_steam_page_tab(self):
        """初始化Steam页面选择选项卡"""
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("--- Steam页面选择 (必须选择3个) ---"))
        layout.addWidget(QLabel("选择要在环形菜单中显示的Steam页面:"))
        layout.addSpacing(10)
        
        self.page_options = {
            'library': '游戏库',
            'store': '商店',
            'community': '社区',
            'workshop': '创意工坊',
            'profile': '个人资料',
            'friends': '好友',
            'downloads': '下载',
            'settings': '设置'
        }
        
        selected_pages = self.config_manager.get("steam_menu_pages", ['library', 'store', 'community'])
        while len(selected_pages) < 3:
            selected_pages.append('library')
        selected_pages = selected_pages[:3]
        
        self.page_combos = []
        labels = ["主选项 (Top 1)", "子选项 1 (Top 2)", "子选项 2 (Top 3)"]
        self.NONE_VALUE = '__none__'
        
        for i in range(3):
            layout.addWidget(QLabel(f"{labels[i]}:"))
            combo = QComboBox()
            
            # 添加"未选择"选项
            combo.addItem("未选择", self.NONE_VALUE)
            
            # 添加所有页面选项
            for page_key, page_name in self.page_options.items():
                combo.addItem(page_name, page_key)
            
            # 设置当前选中的页面
            current_page = selected_pages[i] if i < len(selected_pages) and selected_pages[i] in self.page_options else 'library'
            if i < len(selected_pages) and selected_pages[i] is None:
                current_page = self.NONE_VALUE
            
            index = combo.findData(current_page)
            if index >= 0:
                combo.setCurrentIndex(index)
            
            combo.currentIndexChanged.connect(lambda checked, idx=i: self.on_page_selection_changed(idx))
            
            self.page_combos.append(combo)
            layout.addWidget(combo)
            layout.addSpacing(5)
        
        layout.addStretch()
        self.steam_page_tab.setLayout(layout)
    
    def on_page_selection_changed(self, changed_index):
        """当页面选择改变时，如果重复则将之前的设为未选择"""
        if not hasattr(self, 'page_combos') or len(self.page_combos) != 3:
            return
        
        if changed_index < 0 or changed_index >= len(self.page_combos):
            return
        
        changed_combo = self.page_combos[changed_index]
        selected_value = changed_combo.currentData()
        
        if selected_value == self.NONE_VALUE:
            return
        
        # 检查其他下拉框是否有相同的选择
        for i, combo in enumerate(self.page_combos):
            if i != changed_index:
                combo_value = combo.currentData()
                if combo_value == selected_value:
                    # 找到重复项，将其设置为"未选择"
                    none_index = combo.findData(self.NONE_VALUE)
                    if none_index >= 0:
                        combo.blockSignals(True)
                        combo.setCurrentIndex(none_index)
                        combo.blockSignals(False)

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

        alt_ids = []
        for line in self.alt_id_inputs:
            sid = line.text().strip()
            if sid:
                alt_ids.append(sid)
            if len(alt_ids) >= 3:
                break
        if not self.steam_id_input.text().strip():
            alt_ids = []
        self.config_manager.set("steam_alt_ids", alt_ids)

        self.config_manager.set("steam_api_key", self.api_key_input.text())
        
        # Save Quick Launch Games
        self.config_manager.set("steam_quick_launch_games", self.quick_launch_games)
        
        # Save Steam Menu Pages
        if hasattr(self, 'page_combos') and len(self.page_combos) == 3:
            selected_pages = []
            has_none = False
            none_positions = []
            
            for i, combo in enumerate(self.page_combos):
                data = combo.currentData()
                if data == self.NONE_VALUE:
                    has_none = True
                    none_positions.append(i + 1)
                    selected_pages.append(None)
                else:
                    selected_pages.append(data)
            
            if has_none:
                positions_str = "、".join([f"第{pos}个" for pos in none_positions])
                QMessageBox.warning(
                    self,
                    "提示",
                    f"检测到{positions_str}选项为\"未选择\"。\n\n"
                    "请为所有选项选择有效的Steam页面后再保存。",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            self.config_manager.set("steam_menu_pages", selected_pages)
        
        self.accept()
