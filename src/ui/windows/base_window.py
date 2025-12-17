from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialogButtonBox, QMessageBox
)


class BaseWindow(ABC):
    """
    基础窗口类：统一窗口生命周期、信号管理、UI构建模式。

    设计理念：
    - 统一窗口属性设置（标题、大小、模态等）
    - 标准化信号定义和处理
    - 提供通用的UI构建模式
    - 支持数据更新模式
    - 统一错误处理和状态管理
    """

    # 标准信号 - 子类可扩展
    window_closed = pyqtSignal()
    data_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self,
                 title: str = "",
                 width: int = 500,
                 height: int = 600,
                 modal: bool = False,
                 parent: Optional[QWidget] = None):
        """
        初始化基础窗口。

        Args:
            title: 窗口标题
            width: 默认宽度
            height: 默认高度
            modal: 是否为模态窗口
            parent: 父窗口
        """
        # 根据modal选择基类
        base_cls = QDialog if modal else QWidget
        super().__init__(parent)

        self._window_title = title
        self._default_size = (width, height)
        self._is_modal = modal

        # 状态管理
        self._is_loading = False
        self._current_data = {}

        # UI组件引用
        self._main_layout: Optional[QVBoxLayout] = None
        self._content_widget: Optional[QWidget] = None
        self._status_label: Optional[QLabel] = None
        self._button_layout: Optional[QHBoxLayout] = None

        # 初始化UI
        self._init_window()
        self._setup_ui()
        self._connect_signals()

        # 子类特化初始化
        self._init_subclass()

    def _init_window(self):
        """初始化窗口基本属性"""
        if self._window_title:
            self.setWindowTitle(self._window_title)
        self.resize(*self._default_size)

        if self._is_modal and isinstance(self, QDialog):
            self.setModal(True)

        # 设置窗口标志
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)

    def _setup_ui(self):
        """设置UI布局结构"""
        self._main_layout = QVBoxLayout()
        self.setLayout(self._main_layout)

        # 创建内容区域
        self._content_widget = QWidget()
        self._setup_content_layout()

        # 状态标签（可选）
        self._setup_status_area()

        # 按钮区域（可选）
        self._setup_button_area()

    def _setup_content_layout(self):
        """设置内容布局 - 子类实现"""
        content_layout = self._create_content_layout()
        self._content_widget.setLayout(content_layout)
        self._main_layout.addWidget(self._content_widget)

    @abstractmethod
    def _create_content_layout(self) -> QVBoxLayout:
        """创建内容布局 - 子类必须实现"""
        pass

    def _setup_status_area(self):
        """设置状态显示区域"""
        self._status_label = QLabel()
        self._status_label.setStyleSheet("color: #666; font-size: 12px;")
        self._status_label.hide()  # 默认隐藏
        self._main_layout.addWidget(self._status_label)

    def _setup_button_area(self):
        """设置按钮区域"""
        self._button_layout = QHBoxLayout()
        self._main_layout.addLayout(self._button_layout)

    def _connect_signals(self):
        """连接基础信号"""
        pass

    @abstractmethod
    def _init_subclass(self):
        """子类特化初始化 - 子类实现"""
        pass

    # 公共接口

    def show_status(self, message: str, timeout: int = 0):
        """
        显示状态消息。

        Args:
            message: 状态消息
            timeout: 显示时长（毫秒），0表示永久显示
        """
        if self._status_label:
            self._status_label.setText(message)
            self._status_label.show()

            if timeout > 0:
                QTimer.singleShot(timeout, lambda: self._status_label.hide())

    def hide_status(self):
        """隐藏状态消息"""
        if self._status_label:
            self._status_label.hide()

    def set_loading(self, loading: bool, message: str = "加载中..."):
        """
        设置加载状态。

        Args:
            loading: 是否正在加载
            message: 加载消息
        """
        self._is_loading = loading
        if loading:
            self.show_status(message)
            self.setEnabled(False)
        else:
            self.hide_status()
            self.setEnabled(True)

    def update_data(self, data: Dict[str, Any]):
        """
        更新窗口数据。

        Args:
            data: 数据字典
        """
        self._current_data = data
        self._on_data_updated(data)
        self.data_updated.emit(data)

    def _on_data_updated(self, data: Dict[str, Any]):
        """数据更新处理 - 子类可重写"""
        pass

    def show_error(self, message: str, title: str = "错误"):
        """
        显示错误消息。

        Args:
            message: 错误消息
            title: 对话框标题
        """
        QMessageBox.warning(self, title, message)
        self.error_occurred.emit(message)

    def add_button(self, text: str, callback=None, primary: bool = False) -> QPushButton:
        """
        添加按钮到按钮区域。

        Args:
            text: 按钮文本
            callback: 点击回调
            primary: 是否为主按钮（影响样式）

        Returns:
            创建的按钮
        """
        if not self._button_layout:
            return None

        button = QPushButton(text)
        if primary:
            button.setStyleSheet("font-weight: bold;")

        if callback:
            button.clicked.connect(callback)

        if primary:
            self._button_layout.addWidget(button)
            self._button_layout.addStretch()
        else:
            self._button_layout.addWidget(button)

        return button

    def add_dialog_buttons(self, ok_callback=None, cancel_callback=None):
        """
        添加标准的确定/取消按钮（用于对话框）。

        Args:
            ok_callback: 确定按钮回调
            cancel_callback: 取消按钮回调
        """
        if not isinstance(self, QDialog):
            return

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        if ok_callback:
            button_box.accepted.connect(ok_callback)
        if cancel_callback:
            button_box.rejected.connect(cancel_callback)

        self._main_layout.addWidget(button_box)

    # 窗口事件

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.window_closed.emit()
        super().closeEvent(event)

    # 属性访问器

    @property
    def is_modal(self) -> bool:
        """是否为模态窗口"""
        return self._is_modal

    @property
    def is_loading(self) -> bool:
        """是否正在加载"""
        return self._is_loading

    @property
    def current_data(self) -> Dict[str, Any]:
        """当前数据"""
        return self._current_data.copy()


__all__ = ["BaseWindow"]