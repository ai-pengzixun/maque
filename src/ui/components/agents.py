#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体管理组件
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTableWidget,
    QHeaderView, QAbstractItemView, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox,
    QDialog, QFrame
)
from PySide6.QtCore import Qt
import os
import json
from src.ui.components.config import show_config_editor
from src.jjrj_config import JjrjConfig


# ── Ant Design 风格 QSS ──────────────────────────────────────────────────── #
ANT_TABLE_STYLE = """
QTableWidget {
    border: 1px solid #f0f0f0;
    border-radius: 6px;
    background-color: #ffffff;
    alternate-background-color: #fafafa;
    gridline-color: transparent;
    selection-background-color: transparent;
    outline: none;
}
QTableWidget::item {
    padding: 0px 16px;
    border-bottom: 1px solid #f0f0f0;
    color: rgba(0, 0, 0, 0.85);
    background-color: transparent;
}
QTableWidget::item:alternate {
    background-color: #fafafa;
}
QTableWidget::item:hover {
    background-color: #e6f4ff;
}
QTableWidget::item:selected {
    background-color: #e6f4ff;
    color: rgba(0, 0, 0, 0.85);
}
QHeaderView {
    background-color: #fafafa;
    border: none;
}
QHeaderView::section {
    background-color: #fafafa;
    color: rgba(0, 0, 0, 0.88);
    font-weight: 600;
    font-size: 13px;
    padding: 0px 16px;
    height: 48px;
    border: none;
    border-bottom: 1px solid #f0f0f0;
    border-right: 1px solid #f0f0f0;
}
QHeaderView::section:last {
    border-right: none;
}
QHeaderView::section:hover {
    background-color: #f0f0f0;
}
QTableWidget QScrollBar:vertical {
    width: 6px;
    background: transparent;
}
QTableWidget QScrollBar::handle:vertical {
    background: #d9d9d9;
    border-radius: 3px;
    min-height: 30px;
}
QTableWidget QScrollBar::handle:vertical:hover { background: #bfbfbf; }
QTableWidget QScrollBar::add-line:vertical,
QTableWidget QScrollBar::sub-line:vertical { height: 0; }
QTableWidget QScrollBar:horizontal {
    height: 6px;
    background: transparent;
}
QTableWidget QScrollBar::handle:horizontal {
    background: #d9d9d9;
    border-radius: 3px;
    min-width: 30px;
}
QTableWidget QScrollBar::handle:horizontal:hover { background: #bfbfbf; }
QTableWidget QScrollBar::add-line:horizontal,
QTableWidget QScrollBar::sub-line:horizontal { width: 0; }
"""


# ── 列定义 ───────────────────────────────────────────────────────────────── #
COLUMN_DEFS = [
    {"key": "name",        "label": "名称", "width": 200},
    {"key": "status",      "label": "状态",       "width": 100},
    {"key": "config",      "label": "配置",       "width": 100},
    {"key": "action",      "label": "操作",       "width": 100},
    {"key": "description", "label": "描述",       "width": 200},
]

# 标准入口文件列表
REQUIRED_FILES = ["agent.json", "agent.py"]


class AgentManagement(QWidget):
    """智能体管理类"""

    def __init__(self):
        super().__init__()
        self.agent_info_list = []
        self.callback_handler = None
        self.init_ui()

    # ------------------------------------------------------------------ #
    #  UI 初始化
    # ------------------------------------------------------------------ #
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        title_label = QLabel("智能体管理")
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: rgba(0,0,0,0.85);"
        )
        main_layout.addWidget(title_label)
        main_layout.addWidget(self._build_header())

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索智能体名称或描述…")
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
                outline: none;
            }
            QLineEdit:disabled {
                color: rgba(0, 0, 0, 0.25);
                border-color: #d9d9d9;
                background-color: #f5f5f5;
            }
        """)
        main_layout.addWidget(self.search_edit)

        main_layout.addWidget(self._build_table(), stretch=1)
        main_layout.addWidget(self._build_pagination())

        self.search_edit.textChanged.connect(self._on_search_changed)

    def _build_header(self):
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        desc = QLabel("管理从本地加载或从网络下载的智能体")
        desc.setStyleSheet("font-size: 14px; color: rgba(0,0,0,0.65);")
        layout.addWidget(desc)
        layout.addStretch()

        self.refresh_button = QPushButton("刷新智能体")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff; color: rgba(0,0,0,0.85);
                border: 1px solid #d9d9d9; border-radius: 6px;
                padding: 6px 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #e6f4ff; border-color: #1677ff; color: #1677ff; }
            QPushButton:pressed { background-color: #bae0ff; border-color: #0958d9; color: #0958d9; }
        """)
        layout.addWidget(self.refresh_button)

        self.new_script_button = QPushButton("导入智能体")
        self.new_script_button.setStyleSheet("""
            QPushButton {
                background-color: #1677ff; color: #ffffff;
                border: none; border-radius: 6px;
                padding: 6px 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #4096ff; }
            QPushButton:pressed { background-color: #0958d9; }
        """)
        layout.addWidget(self.new_script_button)
        return w

    def _build_table(self):
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(len(COLUMN_DEFS))
        self.table_widget.setHorizontalHeaderLabels([col["label"] for col in COLUMN_DEFS])
        
        self.table_widget.setShowGrid(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table_widget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table_widget.verticalHeader().setDefaultSectionSize(32)
        self.table_widget.verticalHeader().setVisible(False)

        # 设置列宽
        header = self.table_widget.horizontalHeader()
        for i, col in enumerate(COLUMN_DEFS):
            if i == len(COLUMN_DEFS) - 1:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                self.table_widget.setColumnWidth(i, col["width"])

        self.table_widget.setStyleSheet(ANT_TABLE_STYLE)
        return self.table_widget

    def _build_pagination(self):
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)

        self.pagination_info = QLabel("共 0 条")
        self.pagination_info.setStyleSheet("font-size: 13px; color: rgba(0,0,0,0.45);")
        layout.addWidget(self.pagination_info)
        layout.addStretch()

        btn_normal = """
            QPushButton {
                background-color: #ffffff; color: rgba(0,0,0,0.85);
                border: 1px solid #d9d9d9; border-radius: 6px;
                padding: 4px 12px; font-size: 13px; min-width: 32px;
            }
            QPushButton:hover { border-color: #1677ff; color: #1677ff; }
            QPushButton:disabled { color: rgba(0,0,0,0.25); border-color: #d9d9d9; }
        """
        btn_active = """
            QPushButton {
                background-color: #1677ff; color: #ffffff;
                border: 1px solid #1677ff; border-radius: 6px;
                padding: 4px 12px; font-size: 13px; min-width: 32px;
            }
        """

        self.prev_page_button = QPushButton("‹ 上一页")
        self.prev_page_button.setStyleSheet(btn_normal)
        layout.addWidget(self.prev_page_button)

        self.page_button = QPushButton("1")
        self.page_button.setStyleSheet(btn_active)
        layout.addWidget(self.page_button)

        self.next_page_button = QPushButton("下一页 ›")
        self.next_page_button.setStyleSheet(btn_normal)
        layout.addWidget(self.next_page_button)
        return w

    def _on_search_changed(self, text):
        """搜索文本变化"""
        self._filter_table(text)

    def _filter_table(self, text):
        """根据搜索文本过滤表格"""
        text = text.lower()
        for row in range(self.table_widget.rowCount()):
            name_item = self.table_widget.item(row, 0)
            desc_item = self.table_widget.item(row, 4)
            
            name = name_item.text().lower() if name_item else ""
            desc = desc_item.text().lower() if desc_item else ""
            
            match = text in name or text in desc
            self.table_widget.setRowHidden(row, not match)

    # ------------------------------------------------------------------ #
    #  数据加载
    # ------------------------------------------------------------------ #
    def load_agents(self, agents_dir, callback_handler):
        """从目录加载智能体

        Args:
            agents_dir: 智能体目录路径
            callback_handler: 回调处理器对象，包含 execute_agent 方法
        """
        self.callback_handler = callback_handler
        self.agent_info_list = []

        if not os.path.exists(agents_dir):
            self.table_widget.setRowCount(0)
            self.update_pagination_info(0)
            return

        # 收集智能体数据
        for agent_folder in os.listdir(agents_dir):
            agent_path = os.path.join(agents_dir, agent_folder)
            if not os.path.isdir(agent_path):
                continue
            
            # 检查必需文件是否存在
            if not self._validate_agent_structure(agent_path, agent_folder):
                continue
                
            config_file = os.path.join(agent_path, "agent.json")
            if not os.path.exists(config_file):
                continue
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                name = config.get("name", agent_folder)
                description = config.get("description", "")
                status = config.get("status", "READY")
                robot_file = config.get("robot_file", f"{agent_folder}.robot")

                self.agent_info_list.append(
                    {
                        "name": name, 
                        "agent_path": agent_path,
                        "robot_file": robot_file,
                        "description": description,
                        "status": status
                    }
                )
            except Exception as e:
                print(f"加载智能体 {agent_folder} 失败: {e}")

        # 填充表格
        self._populate_table()
        self.update_pagination_info(len(self.agent_info_list))
    
    def _validate_agent_structure(self, agent_path: str, agent_name: str) -> bool:
        """
        验证智能体结构是否符合规范
        
        Args:
            agent_path: 智能体目录路径
            agent_name: 智能体名称
            
        Returns:
            bool: 结构是否有效
        """
        # 检查必需的基础文件
        for required_file in REQUIRED_FILES:
            file_path = os.path.join(agent_path, required_file)
            if not os.path.exists(file_path):
                print(f"警告: 智能体 '{agent_name}' 缺少必需文件: {required_file}")
                return False
        
        # 检查 agent.json 中指定的 robot_file 是否存在
        config_file = os.path.join(agent_path, "agent.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                robot_file = config.get("robot_file")
                if robot_file:
                    robot_path = os.path.join(agent_path, robot_file)
                    if not os.path.exists(robot_path):
                        print(f"警告: 智能体 '{agent_name}' 缺少 Robot 文件: {robot_file}")
                        return False
                        
                # 检查额外声明的文件
                extra_files = config.get("extra_files", [])
                for extra_file in extra_files:
                    extra_path = os.path.join(agent_path, extra_file)
                    if not os.path.exists(extra_path):
                        print(f"警告: 智能体 '{agent_name}' 缺少声明文件: {extra_file}")
                        
            except Exception as e:
                print(f"验证智能体 '{agent_name}' 配置失败: {e}")
                return False
        
        return True

    def _check_env_configured(self) -> bool:
        """
        检查环境配置是否完成
        
        Returns:
            bool: 环境是否已配置
        """
        return JjrjConfig.is_env_configured()
    
    def _show_env_config_warning(self):
        """显示环境未配置提示并引导用户到设置页面（Ant Design 风格）"""
        dialog = self._create_ant_design_dialog(
            title="环境未配置",
            message="检测到浏览器环境尚未配置完成。\n\n"
                   "请先在【环境设置】中配置 Chrome 浏览器路径。\n\n"
                   "是否立即前往环境设置？",
            confirm_text="前往设置",
            cancel_text="稍后再说",
            is_warning=True
        )

        result = dialog.exec()

        if result == QDialog.Accepted:
            # 尝试切换到环境设置页面
            try:
                from PySide6.QtWidgets import QApplication
                for widget in QApplication.topLevelWidgets():
                    if hasattr(widget, 'main_content'):
                        widget.main_content.show_env_settings()
                        break
            except Exception as e:
                print(f"切换页面失败: {e}")

    def _show_execute_confirm_dialog(self, agent_name: str, robot_file: str) -> bool:
        """
        显示执行确认对话框（Ant Design 风格）

        Args:
            agent_name: 智能体名称
            robot_file: 执行文件名

        Returns:
            bool: 用户是否确认执行
        """
        dialog = self._create_ant_design_dialog(
            title="确认执行",
            message=f"确定要执行智能体【{agent_name}】吗？\n\n"
                   f"执行文件: {robot_file}\n\n"
                   f"执行过程中请勿关闭应用程序。",
            confirm_text="确认执行",
            cancel_text="取消",
            is_warning=False
        )

        result = dialog.exec()
        return result == QDialog.Accepted

    def _create_ant_design_dialog(self, title: str, message: str,
                                   confirm_text: str = "确定",
                                   cancel_text: str = "取消",
                                   is_warning: bool = False) -> QDialog:
        """
        创建 Ant Design 风格的自定义对话框

        Args:
            title: 对话框标题
            message: 对话框消息内容
            confirm_text: 确认按钮文本
            cancel_text: 取消按钮文本
            is_warning: 是否为警告类型（影响图标颜色）

        Returns:
            QDialog: 配置好的对话框实例
        """
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from src.ui.resources.resource_manager import MATERIAL_ICONS

        dialog = QDialog(self)
        dialog.setFixedSize(420, 220)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setAttribute(Qt.WA_TranslucentBackground, True)

        # 主布局（为阴影预留空间）
        main_layout = QVBoxLayout(dialog)
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
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: 600; color: rgba(0,0,0,0.88);")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()

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
        close_btn.clicked.connect(dialog.reject)
        title_bar_layout.addWidget(close_btn)

        container_layout.addWidget(title_bar)

        # 分割线
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #f0f0f0;")
        divider.setFrameShape(QFrame.HLine)
        container_layout.addWidget(divider)

        # 内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(28, 24, 28, 20)
        content_layout.setSpacing(16)

        # 图标 + 消息区域
        msg_row = QHBoxLayout()
        msg_row.setSpacing(12)

        # 图标（警告或信息）
        icon_label = QLabel(MATERIAL_ICONS["close"] if is_warning else "")
        icon_label.setFixedSize(24, 24)
        icon_color = "#faad14" if is_warning else "#1677ff"
        icon_label.setStyleSheet(f"""
            font-family: 'Material Icons';
            font-size: 22px;
            color: {icon_color};
            background: transparent;
        """)
        if not is_warning:
            icon_label.hide()  # 非警告模式隐藏图标
        msg_row.addWidget(icon_label)

        # 消息文本
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            font-size: 14px;
            color: rgba(0,0,0,0.65);
            line-height: 1.5;
            background: transparent;
        """)
        message_label.setWordWrap(True)
        msg_row.addWidget(message_label, stretch=1)

        content_layout.addLayout(msg_row)
        content_layout.addStretch()

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()

        # 取消按钮
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setFixedHeight(36)
        cancel_btn.setMinimumWidth(80)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: rgba(0,0,0,0.85);
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                border-color: #1677ff;
                color: #1677ff;
            }
            QPushButton:pressed {
                background-color: #e6f4ff;
                border-color: #0958d9;
                color: #0958d9;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        # 确认按钮
        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setFixedHeight(36)
        confirm_btn.setMinimumWidth(80)
        btn_bg = "#faad14" if is_warning else "#1677ff"
        btn_hover = "#ffc53d" if is_warning else "#4096ff"
        btn_active = "#d48806" if is_warning else "#0958d9"
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:pressed {{
                background-color: {btn_active};
            }}
        """)
        confirm_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(confirm_btn)

        content_layout.addLayout(button_layout)
        container_layout.addWidget(content_widget)
        main_layout.addWidget(container)

        return dialog

    def _populate_table(self):
        """填充表格数据"""
        self.table_widget.setRowCount(len(self.agent_info_list))
        
        for row, info in enumerate(self.agent_info_list):
            # 名称
            name_item = QTableWidgetItem(info["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 0, name_item)
            
            # 状态
            status_item = QTableWidgetItem(info["status"])
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 1, status_item)
            
            # 描述
            desc_item = QTableWidgetItem(info["description"])
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 4, desc_item)
            
            # 配置按钮
            config_btn = QPushButton("配置")
            config_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff; color: rgba(0,0,0,0.65);
                    border: 1px solid #d9d9d9; border-radius: 4px;
                    padding: 3px 10px; font-size: 12px;
                }
                QPushButton:hover { border-color: #1677ff; color: #1677ff; }
                QPushButton:pressed { border-color: #0958d9; color: #0958d9; }
            """)
            config_btn.clicked.connect(self._create_config_callback(info["agent_path"]))
            self.table_widget.setCellWidget(row, 2, config_btn)
            
            # 执行按钮（带环境检查）
            run_btn = QPushButton("执行")
            run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff; color: rgba(0,0,0,0.65);
                    border: 1px solid #d9d9d9; border-radius: 4px;
                    padding: 3px 10px; font-size: 12px;
                }
                QPushButton:hover { border-color: #1677ff; color: #1677ff; }
                QPushButton:pressed { border-color: #0958d9; color: #0958d9; }
            """)
            run_btn.clicked.connect(
                self._create_execute_callback_with_check(info["agent_path"], info["robot_file"], info["name"])
            )
            self.table_widget.setCellWidget(row, 3, run_btn)

    def _create_config_callback(self, agent_path):
        """创建配置按钮回调"""
        def callback():
            show_config_editor(agent_path, self)
        return callback

    def _create_execute_callback_with_check(self, agent_path, robot_file, agent_name=None):
        """创建执行按钮回调（带环境检查和确认对话框）"""
        def callback():
            # 先检查环境配置
            if not self._check_env_configured():
                self._show_env_config_warning()
                return

            # 显示执行确认对话框
            name = agent_name or os.path.basename(agent_path)
            if not self._show_execute_confirm_dialog(name, robot_file):
                return

            # 用户确认执行
            if self.callback_handler and hasattr(self.callback_handler, 'execute_agent'):
                self.callback_handler.execute_agent(agent_path, robot_file)
        return callback

    def _create_execute_callback(self, agent_path, robot_file):
        """创建执行按钮回调（原始版本，不带环境检查）"""
        def callback():
            if self.callback_handler and hasattr(self.callback_handler, 'execute_agent'):
                self.callback_handler.execute_agent(agent_path, robot_file)
        return callback

    # ------------------------------------------------------------------ #
    #  分页信息
    # ------------------------------------------------------------------ #
    def update_pagination_info(self, total_count):
        self.pagination_info.setText(
            "共 0 条" if total_count == 0 else f"共 {total_count} 条"
        )
