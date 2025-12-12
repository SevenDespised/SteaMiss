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
from PyQt6.QtCore import Qt

class BaseGameListWindow(QDialog):
    """
    游戏列表窗口基类
    提供基于 Tab 的多账号游戏列表展示功能
    """
    def __init__(self, title="游戏列表", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(820, 620)

        self.dataset_tabs = []
        self.current_datasets = []
        
        # 主布局
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Tab 控件
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # 顶部/底部工具栏区域 (子类可添加按钮)
        self.toolbar_layout = QHBoxLayout()
        self.layout.addLayout(self.toolbar_layout)
        

    def update_data(self, datasets, **kwargs):
        """更新数据并刷新显示"""
        self.current_datasets = datasets
        self.on_data_updated(**kwargs)
        self.refresh_tabs()

    def on_data_updated(self, **kwargs):
        """数据更新后的钩子，子类可重写以处理额外数据"""
        pass

    def refresh_tabs(self):
        """刷新所有 Tab"""
        self.tabs.clear()
        self.dataset_tabs = []

        if not self.current_datasets:
            self.show_empty_state()
            return

        self.on_tabs_refresh_start()

        for entry in self.current_datasets:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout()

            # 统计信息标签
            stats_label = QLabel("正在加载数据...")
            tab_layout.addWidget(stats_label)

            # 表格
            table = QTableWidget()
            self.setup_table(table)
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

    def show_empty_state(self):
        """显示空状态"""
        placeholder = QWidget()
        ph_layout = QVBoxLayout()
        msg = QLabel("暂无数据，请先刷新 Steam 统计。")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_layout.addStretch()
        ph_layout.addWidget(msg)
        ph_layout.addStretch()
        placeholder.setLayout(ph_layout)
        self.tabs.addTab(placeholder, "提示")

    def on_tabs_refresh_start(self):
        """Tab 刷新开始前的钩子"""
        pass

    def setup_table(self, table):
        """设置表格列和属性 (子类必须实现)"""
        raise NotImplementedError

    def populate_tab(self, tab_info):
        """填充 Tab 数据 (子类必须实现)"""
        raise NotImplementedError
