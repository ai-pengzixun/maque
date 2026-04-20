#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务列表组件 - Ant Design 风格
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QProgressBar,
    QPushButton, QLabel, QLineEdit
)
from PySide6.QtCore import Qt


# ── 设计 Token（与 agents / sidebar 一致）──────────────────────────────── #
COLOR_PRIMARY      = "#1677ff"
COLOR_PRIMARY_BG   = "#e6f4ff"
COLOR_SUCCESS      = "#52c41a"
COLOR_SUCCESS_BG   = "#f6ffed"
COLOR_ERROR        = "#ff4d4f"
COLOR_ERROR_BG     = "#fff2f0"
COLOR_WARNING      = "#faad14"
COLOR_WARNING_BG   = "#fffbe6"
COLOR_TEXT_TITLE   = "rgba(0,0,0,0.85)"
COLOR_TEXT_NORMAL  = "rgba(0,0,0,0.65)"
COLOR_TEXT_HINT    = "rgba(0,0,0,0.45)"
COLOR_BORDER       = "#f0f0f0"
COLOR_BG_CARD      = "#ffffff"
COLOR_BG_PAGE      = "#f5f5f5"


# ── 任务表格 QSS ──────────────────────────────────────────────────────── #
ANT_TABLE_STYLE = """
QTableWidget {
    border: none;
    background-color: #ffffff;
    alternate-background-color: #fafafa;
    gridline-color: transparent;
    selection-background-color: transparent;
    outline: none;
}
QTableWidget::item {
    padding: 0px 16px;
    border-bottom: 1px solid #f0f0f0;
    color: rgba(0,0,0,0.85);
    background-color: transparent;
}
QTableWidget::item:alternate { background-color: #fafafa; }
QTableWidget::item:hover     { background-color: #e6f4ff; }
QTableWidget::item:selected  { background-color: #e6f4ff; color: rgba(0,0,0,0.85); }
QHeaderView { background-color: #fafafa; border: none; }
QHeaderView::section {
    background-color: #fafafa;
    color: rgba(0,0,0,0.88);
    font-weight: 600;
    font-size: 13px;
    padding: 0px 16px;
    height: 48px;
    border: none;
    border-bottom: 1px solid #f0f0f0;
    border-right: 1px solid #f0f0f0;
}
QHeaderView::section:last { border-right: none; }
QHeaderView::section:hover { background-color: #f0f0f0; }
QTableWidget QScrollBar:vertical {
    width: 6px; background: transparent;
}
QTableWidget QScrollBar::handle:vertical {
    background: #d9d9d9; border-radius: 3px; min-height: 30px;
}
QTableWidget QScrollBar::handle:vertical:hover { background: #bfbfbf; }
QTableWidget QScrollBar::add-line:vertical,
QTableWidget QScrollBar::sub-line:vertical { height: 0; }
QTableWidget QScrollBar:horizontal {
    height: 6px; background: transparent;
}
QTableWidget QScrollBar::handle:horizontal {
    background: #d9d9d9; border-radius: 3px; min-width: 30px;
}
QTableWidget QScrollBar::handle:horizontal:hover { background: #bfbfbf; }
QTableWidget QScrollBar::add-line:horizontal,
QTableWidget QScrollBar::sub-line:horizontal { width: 0; }
"""


# ── 列定义 ───────────────────────────────────────────────────────────────── #
TASK_COLUMN_DEFS = [
    {"key": "name",       "label": "任务名称",   "width": 200, "stretch": False},
    {"key": "created_at", "label": "创建时间",   "width": 160, "stretch": False},
    {"key": "status",     "label": "状态",       "width": 110, "stretch": False},
    {"key": "start_time", "label": "开始执行时间", "width": 160, "stretch": False},
    {"key": "end_time",   "label": "执行完成时间", "width": 160, "stretch": False},
    {"key": "action",     "label": "操作",       "width": 120, "stretch": True},
]


# ── 工具函数 ─────────────────────────────────────────────────────────────── #
def _card_style(border_color=COLOR_BORDER):
    return f"""
        QWidget {{
            background-color: {COLOR_BG_CARD};
            border: 1px solid {border_color};
            border-radius: 8px;
        }}
    """


def _stat_label(text, font_size=12, color=COLOR_TEXT_NORMAL, bold=False):
    lbl = QLabel(text)
    weight = "600" if bold else "normal"
    lbl.setStyleSheet(
        f"font-size: {font_size}px; font-weight: {weight}; color: {color}; background: transparent; border: none;"
    )
    return lbl


def _btn_style_normal():
    return """
        QPushButton {
            background-color: #ffffff; color: rgba(0,0,0,0.85);
            border: 1px solid #d9d9d9; border-radius: 6px;
            padding: 4px 12px; font-size: 13px; min-width: 32px;
        }
        QPushButton:hover { border-color: #1677ff; color: #1677ff; }
        QPushButton:disabled { color: rgba(0,0,0,0.25); border-color: #d9d9d9; }
    """


def _btn_style_primary():
    return """
        QPushButton {
            background-color: #1677ff; color: #ffffff;
            border: none; border-radius: 6px;
            padding: 6px 16px; font-size: 13px;
        }
        QPushButton:hover { background-color: #4096ff; }
        QPushButton:pressed { background-color: #0958d9; }
    """


def _btn_style_active_page():
    return """
        QPushButton {
            background-color: #1677ff; color: #ffffff;
            border: 1px solid #1677ff; border-radius: 6px;
            padding: 4px 10px; font-size: 13px; min-width: 32px;
        }
    """


class TasksUI(QWidget):
    """任务列表页面（Ant Design 风格）"""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {COLOR_BG_PAGE};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # ── 标题行 ──
        main_layout.addWidget(self._build_title_row())

        # ── 统计卡片 ──
        main_layout.addWidget(self._build_stats_row())

        # ── 任务表格卡片 ──
        main_layout.addWidget(self._build_table_card(), stretch=1)

    # ------------------------------------------------------------------ #
    def _build_title_row(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("任务列表")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_TITLE}; background: transparent;"
        )
        layout.addWidget(title)
        layout.addStretch()
        return w

    # ------------------------------------------------------------------ #
    def _build_stats_row(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._stat_card_primary())
        layout.addWidget(self._stat_card_running())
        layout.addWidget(self._stat_card_error())
        return w

    def _stat_card_primary(self):
        """总执行任务卡片 - 蓝色主色调"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_PRIMARY};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(6)

        layout.addWidget(_stat_label("总执行任务", 12, "#ffffff"))
        layout.addWidget(_stat_label("1,284", 32, "#ffffff", bold=True))

        trend = QLabel("↗ +12.5%  本月")
        trend.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.75); background: transparent; border: none;")
        layout.addWidget(trend)
        return card

    def _stat_card_running(self):
        """正在运行卡片"""
        card = QWidget()
        card.setStyleSheet(_card_style())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(6)

        layout.addWidget(_stat_label("正在运行", 12, COLOR_TEXT_NORMAL))
        layout.addWidget(_stat_label("03", 32, COLOR_TEXT_TITLE, bold=True))

        # 进度条
        bar = QProgressBar()
        bar.setValue(30)
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {COLOR_BG_PAGE};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_PRIMARY};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(bar)
        return card

    def _stat_card_error(self):
        """异常停止卡片"""
        card = QWidget()
        card.setStyleSheet(_card_style(border_color="#ffccc7"))
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(6)

        layout.addWidget(_stat_label("异常停止", 12, COLOR_TEXT_NORMAL))
        layout.addWidget(_stat_label("02", 32, COLOR_ERROR, bold=True))

        alert = QLabel("⚠  需要关注")
        alert.setStyleSheet(f"font-size: 12px; color: {COLOR_ERROR}; background: transparent; border: none;")
        layout.addWidget(alert)
        return card

    # ------------------------------------------------------------------ #
    def _build_table_card(self):
        """包含搜索栏 + 表格 + 分页的卡片"""
        card = QWidget()
        card.setStyleSheet(_card_style())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 卡片头部（标题 + 搜索 + 新建）
        layout.addWidget(self._build_table_header())

        # 分割线
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {COLOR_BORDER};")
        layout.addWidget(divider)

        # 表格
        layout.addWidget(self._build_table(), stretch=1)

        # 分割线
        divider2 = QWidget()
        divider2.setFixedHeight(1)
        divider2.setStyleSheet(f"background-color: {COLOR_BORDER};")
        layout.addWidget(divider2)

        # 分页
        layout.addWidget(self._build_pagination())
        return card

    def _build_table_header(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        title = QLabel("自动化流列表")
        title.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_TITLE}; background: transparent;"
        )
        layout.addWidget(title)
        layout.addStretch()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索任务名称…")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                height: 32px;
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
                color: rgba(0, 0, 0, 0.85);
            }
            QLineEdit:hover {
                border-color: #1677ff;
            }
            QLineEdit:focus {
                border-color: #1677ff;
            }
        """)
        layout.addWidget(self.search_edit)

        new_btn = QPushButton("+ 新建任务")
        new_btn.setStyleSheet(_btn_style_primary())
        layout.addWidget(new_btn)
        return w

    def _build_table(self):
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(len(TASK_COLUMN_DEFS))
        self.table_widget.setHorizontalHeaderLabels([col["label"] for col in TASK_COLUMN_DEFS])
        
        self.table_widget.setShowGrid(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table_widget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table_widget.verticalHeader().setDefaultSectionSize(48)
        self.table_widget.verticalHeader().setVisible(False)

        # 设置列宽
        header = self.table_widget.horizontalHeader()
        for i, col in enumerate(TASK_COLUMN_DEFS):
            if col["stretch"]:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                self.table_widget.setColumnWidth(i, col["width"])

        self.table_widget.setStyleSheet(ANT_TABLE_STYLE)

        # 搜索联动
        self.search_edit.textChanged.connect(self._on_search_changed)
        return self.table_widget

    def _on_search_changed(self, text):
        """搜索文本变化时过滤表格"""
        text = text.lower()
        for row in range(self.table_widget.rowCount()):
            name_item = self.table_widget.item(row, 0)
            if name_item:
                match = text in name_item.text().lower()
                self.table_widget.setRowHidden(row, not match)

    def _build_pagination(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)

        self.pagination_info = QLabel("共 0 条")
        self.pagination_info.setStyleSheet(
            f"font-size: 13px; color: {COLOR_TEXT_HINT}; background: transparent;"
        )
        layout.addWidget(self.pagination_info)
        layout.addStretch()

        self.prev_btn = QPushButton("‹ 上一页")
        self.prev_btn.setStyleSheet(_btn_style_normal())
        layout.addWidget(self.prev_btn)

        self.page1_btn = QPushButton("1")
        self.page1_btn.setStyleSheet(_btn_style_active_page())
        layout.addWidget(self.page1_btn)

        for n in ("2", "3"):
            btn = QPushButton(n)
            btn.setStyleSheet(_btn_style_normal())
            layout.addWidget(btn)

        self.next_btn = QPushButton("下一页 ›")
        self.next_btn.setStyleSheet(_btn_style_normal())
        layout.addWidget(self.next_btn)
        return w

    # ── 公共接口 ──────────────────────────────────────────────────────── #
    def load_tasks(self, task_data_list: list):
        """加载任务数据并渲染行按钮

        Args:
            task_data_list: list of dict，字段与 TASK_COLUMN_DEFS key 对应
        """
        self.table_widget.setRowCount(len(task_data_list))
        
        for row, data in enumerate(task_data_list):
            # 填充数据
            for col_idx, col_def in enumerate(TASK_COLUMN_DEFS):
                key = col_def["key"]
                if key == "action":
                    # 操作列添加按钮
                    btn = QPushButton("查看详情")
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #ffffff; color: rgba(0,0,0,0.65);
                            border: 1px solid #d9d9d9; border-radius: 4px;
                            padding: 3px 10px; font-size: 12px;
                        }
                        QPushButton:hover { border-color: #1677ff; color: #1677ff; }
                    """)
                    self.table_widget.setCellWidget(row, col_idx, btn)
                else:
                    value = data.get(key, "")
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table_widget.setItem(row, col_idx, item)
        
        self.pagination_info.setText(f"共 {len(task_data_list)} 条")
