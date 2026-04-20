#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体配置编辑组件 - Ant Design 风格
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog,
    QScrollArea, QFrame, QLabel, QTextEdit,
    QPushButton, QLineEdit, QCheckBox, QSpinBox,
    QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import json
import os


# ── 设计 Token（与 agents 一致）──────────────────────────────────────── #
COLOR_PRIMARY      = "#1677ff"
COLOR_PRIMARY_BG   = "#e6f4ff"
COLOR_SUCCESS      = "#52c41a"
COLOR_ERROR        = "#ff4d4f"
COLOR_TEXT_TITLE   = "rgba(0,0,0,0.85)"
COLOR_TEXT_NORMAL  = "rgba(0,0,0,0.65)"
COLOR_TEXT_HINT    = "rgba(0,0,0,0.45)"
COLOR_BORDER       = "#f0f0f0"
COLOR_BG_CARD      = "#ffffff"


def _btn_style_normal():
    return """
        QPushButton {
            background-color: #ffffff; color: rgba(0,0,0,0.85);
            border: 1px solid #d9d9d9; border-radius: 6px;
            padding: 6px 16px; font-size: 13px;
        }
        QPushButton:hover { border-color: #1677ff; color: #1677ff; }
        QPushButton:pressed { background-color: #bae0ff; border-color: #0958d9; color: #0958d9; }
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


def _card_style():
    return f"""
        QWidget {{
            background-color: {COLOR_BG_CARD};
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
        }}
    """


class ConfigEditor(QDialog):
    """智能体配置编辑器 - Ant Design 风格带窗口控制按钮"""

    def __init__(self, agent_path: str, parent=None):
        super().__init__(parent)
        self.agent_path = agent_path
        self.config_file = os.path.join(agent_path, "agent.json")
        self.config_data = {}
        self.widgets = {}

        # 设置无边框窗口 + 阴影效果（与 main_window 保持一致）
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setMinimumWidth(650)
        self.setMinimumHeight(550)

        self.init_ui()
        self.load_config()

    def init_ui(self):
        # 主布局（为阴影预留空间）
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(0)

        # 创建带阴影和圆角的容器
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 10px;
            }
        """)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 90))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)

        # 容器内部布局
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 标题栏（包含窗口控制按钮）
        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet("background-color: transparent;")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(20, 0, 12, 0)
        title_bar_layout.setSpacing(8)

        # 窗口标题
        title_label = QLabel("智能体配置")
        title_label.setStyleSheet("font-size: 15px; font-weight: 600; color: rgba(0,0,0,0.88);")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()

        # 导入 Material Icons
        from src.ui.resources.resource_manager import MATERIAL_ICONS

        # 最大化按钮
        self.max_btn = QPushButton(MATERIAL_ICONS["fullscreen"])
        self.max_btn.setFixedSize(28, 28)
        self.max_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(0,0,0,0.45);
                border: none;
                border-radius: 4px;
                font-family: 'Material Icons';
                font-size: 18px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.06);
                color: rgba(0,0,0,0.85);
            }
        """)
        self.max_btn.clicked.connect(self._toggle_maximize)
        title_bar_layout.addWidget(self.max_btn)

        # 关闭按钮
        close_btn = QPushButton(MATERIAL_ICONS["close"])
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(0,0,0,0.45);
                border: none;
                border-radius: 4px;
                font-family: 'Material Icons';
                font-size: 18px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #ff4d4f;
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(close_btn)

        container_layout.addWidget(title_bar)

        # 分割线
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {COLOR_BORDER};")
        divider.setFrameShape(QFrame.HLine)
        container_layout.addWidget(divider)

        # 内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(16)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        scroll.setWidget(self.content_widget)
        content_layout.addWidget(scroll, stretch=1)

        # 底部按钮区域
        button_row = QWidget()
        button_row.setStyleSheet("background: transparent;")
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 12, 0, 0)
        button_layout.setSpacing(12)
        button_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet(_btn_style_normal())
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.setStyleSheet(_btn_style_primary())
        self.save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_btn)

        content_layout.addWidget(button_row)
        container_layout.addWidget(content_widget)
        main_layout.addWidget(container)

    def _toggle_maximize(self):
        """切换窗口最大化/还原状态"""
        from src.ui.resources.resource_manager import MATERIAL_ICONS
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setText(MATERIAL_ICONS["fullscreen"])
        else:
            self.showMaximized()
            self.max_btn.setText(MATERIAL_ICONS["close_fullscreen"])

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
            else:
                self.config_data = {}
            self.render_config()
        except Exception as e:
            error_label = QLabel(f"加载配置失败: {str(e)}")
            error_label.setStyleSheet(f"color: {COLOR_ERROR}; padding: 20px;")
            self.content_layout.addWidget(error_label)

    def render_config(self):
        """根据配置数据动态渲染控件"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.widgets = {}

        if not self.config_data:
            empty_label = QLabel("暂无配置项")
            empty_label.setStyleSheet(f"color: {COLOR_TEXT_HINT}; padding: 20px;")
            self.content_layout.addWidget(empty_label)
            return

        for key, value in self.config_data.items():
            self._render_field(key, value)

        self.content_layout.addStretch()

    def _render_field(self, key: str, value):
        """渲染单个字段"""
        field_card = QWidget()
        field_card.setStyleSheet(_card_style())
        field_layout = QVBoxLayout(field_card)
        field_layout.setContentsMargins(16, 12, 16, 12)
        field_layout.setSpacing(8)

        # 标签
        label = QLabel(key)
        label.setStyleSheet(
            f"font-size: 13px; font-weight: 500; color: {COLOR_TEXT_TITLE}; background: transparent;"
        )
        field_layout.addWidget(label)

        # 根据值类型渲染不同的控件
        if isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
            self.widgets[key] = (widget, bool)
        elif isinstance(value, int):
            widget = QSpinBox()
            widget.setRange(-1000000, 1000000)
            widget.setValue(value)
            widget.setStyleSheet("""
                QSpinBox {
                    height: 32px;
                    background-color: #ffffff;
                    border: 1px solid #d9d9d9;
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 13px;
                    color: rgba(0, 0, 0, 0.85);
                }
                QSpinBox:hover {
                    border-color: #1677ff;
                }
                QSpinBox:focus {
                    border-color: #1677ff;
                }
            """)
            self.widgets[key] = (widget, int)
        elif isinstance(value, list):
            # 数组类型使用多行输入框（每行一个元素）
            widget = self._create_list_editor(value)
            self.widgets[key] = (widget, 'list')
        elif isinstance(value, dict):
            # 字典类型使用文本编辑器
            widget = QTextEdit()
            widget.setPlainText(json.dumps(value, ensure_ascii=False, indent=2))
            widget.setStyleSheet("""
                QTextEdit {
                    background-color: #ffffff;
                    border: 1px solid #d9d9d9;
                    border-radius: 6px;
                    padding: 12px;
                    font-family: "Consolas", "JetBrains Mono", monospace;
                    font-size: 12px;
                    color: rgba(0, 0, 0, 0.85);
                }
                QTextEdit:hover {
                    border-color: #1677ff;
                }
                QTextEdit:focus {
                    border-color: #1677ff;
                }
            """)
            self.widgets[key] = (widget, 'json')
        else:
            # 默认字符串类型
            widget = QLineEdit(str(value))
            widget.setStyleSheet("""
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
            self.widgets[key] = (widget, str)

        field_layout.addWidget(widget)
        self.content_layout.addWidget(field_card)

    def _create_list_editor(self, values: list) -> QWidget:
        """
        创建列表编辑器（多行 input 方式）

        Args:
            values: 列表值

        Returns:
            包含多个 QLineEdit 的容器 Widget
        """
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.list_inputs = []

        for i, val in enumerate(values):
            row = self._create_list_input_row(str(val), i)
            layout.addWidget(row)

        # 添加按钮行
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        add_btn = QPushButton("+ 添加项")
        add_btn.setFixedHeight(28)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1677ff;
                border: 1px dashed #1677ff;
                border-radius: 4px;
                padding: 0 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e6f4ff;
            }
        """)
        add_btn.clicked.connect(lambda: self._add_list_item(layout))
        btn_row.addWidget(add_btn)
        btn_row.addStretch()

        layout.addLayout(btn_row)

        # 保存 layout 引用以便后续添加项目
        container.layout_ref = layout

        return container

    def _create_list_input_row(self, value: str, index: int) -> QWidget:
        """创建单行列表输入框"""
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 序号标签
        num_label = QLabel(f"{index + 1}.")
        num_label.setFixedWidth(24)
        num_label.setStyleSheet(
            f"font-size: 12px; color: {COLOR_TEXT_HINT}; background: transparent;"
        )
        layout.addWidget(num_label)

        # 输入框
        line_edit = QLineEdit(value)
        line_edit.setStyleSheet("""
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
           LineEdit:focus {
                border-color: #1677ff;
            }
        """)
        layout.addWidget(line_edit, stretch=1)

        # 删除按钮
        del_btn = QPushButton("×")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(0,0,0,0.45);
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fff1f0;
                color: #ff4d4f;
            }
        """)
        del_btn.clicked.connect(lambda: self._remove_list_item(row))
        layout.addWidget(del_btn)

        return row

    def _add_list_item(self, parent_layout):
        """添加新的列表项"""
        index = parent_layout.count() - 1  # 减去按钮行
        new_row = self._create_list_input_row("", index)
        parent_layout.insertLayout(index, new_row.layout() if hasattr(new_row, 'layout') else QHBoxLayout(new_row))

    def _remove_list_item(self, row_widget):
        """移除列表项"""
        row_widget.deleteLater()

    def _collect_list_values(self, list_widget) -> list:
        """从列表编辑器收集值"""
        values = []
        layout = list_widget.layout()

        for i in range(layout.count() - 1):  # 排除最后的添加按钮行
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QWidget) and widget.layout():
                    inner_layout = widget.layout()
                    for j in range(inner_layout.count()):
                        inner_item = inner_layout.itemAt(j)
                        if inner_item and inner_item.widget() and isinstance(inner_item.widget(), QLineEdit):
                            text = inner_item.widget().text().strip()
                            if text:
                                values.append(text)

        return values

    def collect_config(self):
        """从控件收集配置数据"""
        new_config = {}
        for key, (widget, value_type) in self.widgets.items():
            if value_type == bool:
                new_config[key] = widget.isChecked()
            elif value_type == int:
                new_config[key] = widget.value()
            elif value_type == 'list':
                new_config[key] = self._collect_list_values(widget)
            elif value_type == 'json':
                try:
                    new_config[key] = json.loads(widget.toPlainText())
                except:
                    new_config[key] = widget.toPlainText()
            elif value_type == str:
                new_config[key] = widget.text()
            else:
                new_config[key] = widget.text()
        return new_config

    def save_config(self):
        """保存配置文件"""
        try:
            new_config = self.collect_config()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            self.config_data = new_config
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存配置失败: {str(e)}")


def show_config_editor(agent_path: str, parent=None):
    """显示配置编辑器弹窗"""
    editor = ConfigEditor(agent_path, parent)
    return editor.exec()
