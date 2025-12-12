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
from PyQt6.QtCore import pyqtSignal

class SettingsDialog(QDialog):
    request_save = pyqtSignal(dict)
    request_search_games = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("功能设置")
        self.resize(500, 600) # 稍微调大一点
        
        # 动态存储控件引用
        self.alt_id_inputs = []
        self.quick_launch_games = [None, None, None]
        
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

    def load_settings(self, config):
        """加载配置到 UI"""
        # Hello
        self.hello_input.setText(config.get("say_hello_content", "你好！"))
        
        # Paths
        paths = config.get("explorer_paths", ["C:/", "C:/", "C:/"])
        aliases = config.get("explorer_path_aliases", ["", "", ""])
        for i in range(3):
            if i < len(paths): self.path_inputs[i].setText(paths[i])
            if i < len(aliases): self.alias_inputs[i].setText(aliases[i])
            
        # Steam
        self.steam_id_input.setText(config.get("steam_id", ""))
        self.api_key_input.setText(config.get("steam_api_key", ""))
        
        # Alt IDs
        self.clear_all_alt_inputs()
        alt_ids = config.get("steam_alt_ids", [])
        if isinstance(alt_ids, list):
            for sid in alt_ids[:3]:
                self.add_alt_id_input(sid)
                
        # Quick Launch
        self.quick_launch_games = config.get("steam_quick_launch_games", [None, None, None])
        if not isinstance(self.quick_launch_games, list):
            self.quick_launch_games = [None, None, None]
        while len(self.quick_launch_games) < 3:
            self.quick_launch_games.append(None)
        self._update_quick_launch_labels()
        
        # Steam Pages
        selected_pages = config.get("steam_menu_pages", ['library', 'store', 'community'])
        for i, combo in enumerate(self.page_combos):
            page = selected_pages[i] if i < len(selected_pages) else 'library'
            if page is None: page = self.NONE_VALUE
            index = combo.findData(page)
            if index >= 0:
                combo.setCurrentIndex(index)

    def init_hello_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("自定义打招呼内容:"))
        self.hello_input = QLineEdit()
        layout.addWidget(self.hello_input)
        layout.addStretch()
        self.hello_tab.setLayout(layout)

    def init_func_tab(self):
        layout = QVBoxLayout()
        
        # 路径设置
        layout.addWidget(QLabel("--- 快捷路径设置 ---"))
        
        self.path_inputs = []
        self.alias_inputs = []
        labels = ["主路径 (Top 1)", "副路径 1 (Top 2)", "副路径 2 (Top 3)"]
        
        for i in range(3):
            layout.addWidget(QLabel(f"{labels[i]}:"))
            
            row_layout = QHBoxLayout()
            
            path_inp = QLineEdit()
            path_inp.setPlaceholderText("路径 (例如 C:/)")
            self.path_inputs.append(path_inp)
            
            alias_inp = QLineEdit()
            alias_inp.setPlaceholderText("显示名称 (可选)")
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

        # API Key
        layout.addSpacing(10)
        layout.addWidget(QLabel("Steam Web API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("在此输入你的 API Key")
        # 设置为密码模式，进行脱敏显示
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
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

        # 显示当前配置的3个槽位
        self.slot_labels = []
        for i in range(3):
            lbl = QLabel(f"槽位{i+1}: 默认 (Top {i+1})")
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

    def _update_quick_launch_labels(self):
        for i in range(3):
            game = self.quick_launch_games[i]
            name = game.get("name", "未设置") if game else f"默认 (Top {i+1})"
            self.slot_labels[i].setText(f"槽位{i+1}: {name}")

    def assign_to_slot(self, idx):
        if not self.selected_game:
            return
        self.quick_launch_games[idx] = self.selected_game
        self._update_quick_launch_labels()

    def clear_slot_dialog(self):
        for i in range(3):
            self.quick_launch_games[i] = None
        self._update_quick_launch_labels()

    def search_games(self):
        keyword = self.search_input.text()
        if not keyword:
            return
        self.game_list.clear()
        self.game_list.addItem("正在搜索...")
        self.request_search_games.emit(keyword)

    def update_search_results(self, results):
        self.game_list.clear()
        if not results:
            self.game_list.addItem("未找到匹配的游戏")
            return
            
        for game in results:
            name = game.get("name", "Unknown")
            appid = game.get("appid")
            self.game_list.addItem(f"{name} | {appid}")

    def on_game_selected(self, item):
        text = item.text()
        if "|" in text:
            name, appid = text.split(" | ")
            self.selected_game = {"name": name.strip(), "appid": int(appid)}

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
            'downloads': '下载',
            'settings': '设置'
        }
        
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
        settings = {}
        
        # Save Hello Content
        settings["say_hello_content"] = self.hello_input.text()
        
        # Save Explorer Paths
        settings["explorer_paths"] = [inp.text() for inp in self.path_inputs]
        settings["explorer_path_aliases"] = [inp.text() for inp in self.alias_inputs]
        
        # Save Steam Config
        settings["steam_id"] = self.steam_id_input.text()

        alt_ids = []
        for line in self.alt_id_inputs:
            sid = line.text().strip()
            if sid:
                alt_ids.append(sid)
            if len(alt_ids) >= 3:
                break
        if not self.steam_id_input.text().strip():
            alt_ids = []
        settings["steam_alt_ids"] = alt_ids

        settings["steam_api_key"] = self.api_key_input.text()
        
        # Save Quick Launch Games
        settings["steam_quick_launch_games"] = self.quick_launch_games
        
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
            
            settings["steam_menu_pages"] = selected_pages
        
        self.request_save.emit(settings)
        self.accept()
