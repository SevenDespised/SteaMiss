from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFontMetrics, QTextLayout
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class DiscountItemWidget(QWidget):
    def __init__(self, game_data, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        name_label = QLabel(game_data["name"])
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label, 1)

        discount_label = QLabel(f"-{game_data['discount_pct']}%")
        discount_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 14px; background-color: #4c6b22; padding: 4px; border-radius: 4px;"
        )
        discount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        discount_label.setFixedWidth(60)
        layout.addWidget(discount_label)

        price_label = QLabel(game_data["price"])
        price_label.setStyleSheet("color: #333; font-weight: bold;")
        price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price_label.setFixedWidth(80)
        layout.addWidget(price_label)

        btn = QPushButton("查看")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedWidth(60)
        btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"https://store.steampowered.com/app/{game_data['appid']}")))
        layout.addWidget(btn)

        self.setLayout(layout)


class NewsItemWidget(QWidget):
    def __init__(self, news_data: dict, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        self._full_title = str(news_data.get("title", "(无标题)"))
        self._title_label = QLabel()
        self._title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        self._title_label.setWordWrap(True)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._title_label.setToolTip(self._full_title)
        layout.addWidget(self._title_label)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)

        source = news_data.get("source", "(未知源)")
        source_label = QLabel(f"源：{source}")
        source_label.setStyleSheet("color: #666; font-size: 12px;")
        meta_row.addWidget(source_label)

        pub_date = news_data.get("pub_date", "")
        if pub_date:
            date_label = QLabel(pub_date)
            date_label.setStyleSheet("color: #888; font-size: 12px;")
            date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            meta_row.addStretch(1)
            meta_row.addWidget(date_label)
        else:
            meta_row.addStretch(1)

        layout.addLayout(meta_row)
        self.setLayout(layout)

        self._update_title_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_title_text()

    def _update_title_text(self) -> None:
        width = max(0, self._title_label.width())
        if width <= 0:
            self._title_label.setText(self._full_title)
            return

        clamped = _elide_to_lines(self._full_title, self._title_label.font(), width, max_lines=2)
        self._title_label.setText(clamped)


def _elide_to_lines(text: str, font, width: int, *, max_lines: int) -> str:
    text = (text or "").strip()
    if not text or max_lines <= 0:
        return ""
    if max_lines == 1:
        return QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, width)

    layout = QTextLayout(text, font)
    layout.beginLayout()

    line_slices: list[tuple[int, int]] = []
    while True:
        line = layout.createLine()
        if not line.isValid():
            break
        line.setLineWidth(width)
        line_slices.append((line.textStart(), line.textLength()))
        if len(line_slices) >= max_lines:
            break

    layout.endLayout()

    if not line_slices:
        return QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, width)

    if len(line_slices) < max_lines and sum(l for _, l in line_slices) >= len(text):
        return text

    kept_lines: list[str] = []
    for start, length in line_slices[: max_lines - 1]:
        kept_lines.append(text[start : start + length].rstrip())

    last_start = line_slices[max_lines - 1][0]
    remaining = text[last_start:].lstrip()
    last_line = QFontMetrics(font).elidedText(remaining, Qt.TextElideMode.ElideRight, width)
    kept_lines.append(last_line)
    return "\n".join([ln for ln in kept_lines if ln])


class EpicFreeGameItemWidget(QWidget):
    def __init__(self, game_data: dict, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title_label = QLabel(game_data.get("title", "(未命名游戏)"))
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        period = game_data.get("period", "")
        if period:
            period_label = QLabel(f"有效期：{period}")
        else:
            period_label = QLabel("有效期：—")
        period_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(period_label)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.addStretch(1)

        url = game_data.get("url")
        open_btn = QPushButton("打开领取页面")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.setEnabled(bool(url))
        if url:
            open_btn.clicked.connect(lambda checked=False, u=url: QDesktopServices.openUrl(QUrl(u)))
        btn_row.addWidget(open_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)


class InfoWindow(QWidget):
    request_refresh = pyqtSignal()
    request_news_refresh = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("信息门户")
        self.resize(550, 600)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.news_tab = self._build_news_tab()
        self.discount_tab = self._build_discount_tab()
        self.epic_tab = self._build_epic_tab()

        self.tabs.addTab(self.news_tab, "新闻")
        self.tabs.addTab(self.discount_tab, "折扣")
        self.tabs.addTab(self.epic_tab, "Epic免费游戏")

        self.update_news_data([])
        self.update_data([])
        self.update_epic_free_games_data([])

    def _build_discount_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        title = QLabel("愿望单/关注游戏中的打折游戏 (Top 10)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet("QListWidget::item { border-bottom: 1px solid #eee; }")
        layout.addWidget(self.list_widget)

        self.refresh_btn = QPushButton("刷新数据")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        self.refresh_btn.setMinimumHeight(40)
        layout.addWidget(self.refresh_btn)

        tab.setLayout(layout)
        return tab

    def _build_news_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        header = QLabel("RSS 新闻")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.news_list_widget = QListWidget()
        self.news_list_widget.setAlternatingRowColors(True)
        self.news_list_widget.setStyleSheet("QListWidget::item { border-bottom: 1px solid #eee; }")
        self.news_list_widget.currentRowChanged.connect(self._on_news_selection_changed)
        splitter.addWidget(self.news_list_widget)

        self.news_detail = QTextBrowser()
        self.news_detail.setOpenExternalLinks(True)
        self.news_detail.setHtml(
            "<h3>暂无新闻</h3>"
            "<p>将会在左侧列表展示新闻条目，并在每条条目中标注 <b>源：RSS源名称</b>。</p>"
        )
        splitter.addWidget(self.news_detail)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 5)
        layout.addWidget(splitter, 1)

        self.news_refresh_btn = QPushButton("刷新新闻")
        self.news_refresh_btn.setMinimumHeight(40)
        self.news_refresh_btn.clicked.connect(self._on_news_refresh_clicked)
        layout.addWidget(self.news_refresh_btn)

        tab.setLayout(layout)
        return tab

    def _build_epic_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        header = QLabel("Epic 免费游戏")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        self.epic_list_widget = QListWidget()
        self.epic_list_widget.setAlternatingRowColors(True)
        self.epic_list_widget.setStyleSheet("QListWidget::item { border-bottom: 1px solid #eee; }")
        layout.addWidget(self.epic_list_widget)

        hint = QLabel("展示 Epic 当前/即将免费游戏（时间按北京时间）。")
        hint.setStyleSheet("color: #666; font-size: 12px; margin: 6px 10px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        tab.setLayout(layout)
        return tab

    def _on_refresh_clicked(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("正在获取愿望单数据...")
        self.request_refresh.emit()

        from PyQt6.QtCore import QTimer

        QTimer.singleShot(60000, lambda: self.refresh_btn.setEnabled(True))
        QTimer.singleShot(60000, lambda: self.refresh_btn.setText("刷新数据"))

    def update_data(self, games):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新数据")
        self.list_widget.clear()

        if not games:
            item = QListWidgetItem("暂无打折推荐或数据加载失败")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_widget.addItem(item)
            return

        for game in games:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 70))
            widget = DiscountItemWidget(game)
            self.list_widget.setItemWidget(item, widget)

    def on_fetch_error(self):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新数据")

    def _on_news_refresh_clicked(self):
        if hasattr(self, "news_refresh_btn"):
            self.news_refresh_btn.setEnabled(False)
            self.news_refresh_btn.setText("正在获取新闻...")
        self.request_news_refresh.emit(True)

    def update_news_data(self, news_items: list[dict]):
        self._news_items = news_items or []
        self.news_list_widget.clear()

        if hasattr(self, "news_refresh_btn"):
            self.news_refresh_btn.setEnabled(True)
            self.news_refresh_btn.setText("刷新新闻")

        if not self._news_items:
            item = QListWidgetItem("暂无新闻")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.news_list_widget.addItem(item)
            self.news_detail.setHtml("<h3>暂无新闻</h3><p>等待后续接入 RSS 数据。</p>")
            return

        for entry in self._news_items:
            row_item = QListWidgetItem(self.news_list_widget)
            row_item.setSizeHint(QSize(0, 88))
            widget = NewsItemWidget(entry)
            self.news_list_widget.setItemWidget(row_item, widget)

        self.news_list_widget.setCurrentRow(0)

    def _on_news_selection_changed(self, row: int):
        if not hasattr(self, "_news_items"):
            return
        if row < 0 or row >= len(self._news_items):
            return

        entry = self._news_items[row]
        title = entry.get("title", "(无标题)")
        source = entry.get("source", "(未知源)")
        pub_date = entry.get("pub_date", "")
        link = entry.get("link", "")
        summary = entry.get("summary", "")

        parts = [f"<h3>{title}</h3>"]
        parts.append(f"<p><b>源：</b>{source}</p>")
        if pub_date:
            parts.append(f"<p><b>时间：</b>{pub_date}</p>")
        if link:
            parts.append(f"<p><a href=\"{link}\">打开原文</a></p>")
        parts.append(f"<hr/><p>{summary or '（此处为正文/摘要占位）'}</p>")

        self.news_detail.setHtml("".join(parts))

    def on_news_fetch_error(self, message: str = ""):
        if hasattr(self, "news_refresh_btn"):
            self.news_refresh_btn.setEnabled(True)
            self.news_refresh_btn.setText("刷新新闻")
        msg = (message or "新闻获取失败").strip()
        self.news_detail.setHtml(f"<h3>获取新闻失败</h3><p>{msg}</p>")

    def update_epic_free_games_data(self, games: list[dict]):
        self.epic_list_widget.clear()

        if not games:
            item = QListWidgetItem("暂无 Epic 免费游戏（UI占位）")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.epic_list_widget.addItem(item)
            return

        for game in games:
            row_item = QListWidgetItem(self.epic_list_widget)
            row_item.setSizeHint(QSize(0, 84))
            widget = EpicFreeGameItemWidget(game)
            self.epic_list_widget.setItemWidget(row_item, widget)


__all__ = ["InfoWindow"]
