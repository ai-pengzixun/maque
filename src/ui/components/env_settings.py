#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境设置页面 - Ant Design 风格
用于配置 Chrome 浏览器路径和用户数据路径
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFileDialog, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
import json
import os


# ── 设计 Token（与 sidebar、config 保持一致）──────────────────────────────── #
COLOR_PRIMARY      = "#1677ff"
COLOR_PRIMARY_BG   = "#e6f4ff"
COLOR_SUCCESS      = "#52c41a"
COLOR_ERROR        = "#ff4d4f"
COLOR_TEXT_TITLE   = "rgba(0,0,0,0.85)"
COLOR_TEXT_NORMAL  = "rgba(0,0,0,0.65)"
COLOR_TEXT_HINT    = "rgba(0,0,0,0.45)"
COLOR_BORDER       = "#f0f0f0"
COLOR_BG_CARD      = "#ffffff"
COLOR_BG_PAGE      = "#f5f5f5"


def _card_style():
    return f"""
        QFrame {{
            background-color: {COLOR_BG_CARD};
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
        }}
    """


def _input_style():
    return """
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
    """


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


class EnvSettings(QWidget):
    """环境设置页面 - 配置 Chrome 路径"""

    # 设置键名常量
    KEY_CHROME_PATH = "chrome_path"
    KEY_USER_DATA_PATH = "user_data_path"

    def __init__(self):
        super().__init__()

        self.setStyleSheet(f"background-color: {COLOR_BG_PAGE};")
        self.init_ui()
        self.load_config()

    def init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 页面标题
        title = QLabel("环境设置")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_TITLE}; background: transparent;"
        )
        main_layout.addWidget(title)

        # 副标题说明
        subtitle = QLabel("配置 Chrome 浏览器运行环境")
        subtitle.setStyleSheet(
            f"font-size: 13px; color: {COLOR_TEXT_HINT}; background: transparent; margin-bottom: 8px;"
        )
        main_layout.addWidget(subtitle)

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
        self.content_layout.setSpacing(16)

        # Chrome 路径配置卡片
        self.chrome_card = self._build_path_card(
            title="Chrome 浏览器路径",
            description="请选择 Chrome 浏览器的可执行文件路径（chrome.exe）",
            placeholder="例如: C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            is_file=True,
            file_filter="可执行文件 (*.exe)"
        )
        self.content_layout.addWidget(self.chrome_card)

        # 用户数据路径配置卡片
        self.user_data_card = self._build_path_card(
            title="用户数据目录",
            description="请选择 Chrome 用户数据存储目录（User Data 文件夹）",
            placeholder="例如: C:\\Users\\Username\\AppData\\Local\\Google\\Chrome\\User Data",
            is_file=False
        )
        self.content_layout.addWidget(self.user_data_card)

        # 提示信息卡片
        hint_card = self._build_hint_card()
        self.content_layout.addWidget(hint_card)

        self.content_layout.addStretch()
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll, stretch=1)

        # 底部按钮区域
        button_row = QWidget()
        button_row.setStyleSheet("background: transparent;")
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(12)
        button_layout.addStretch()

        self.reset_btn = QPushButton("重置")
        self.reset_btn.setStyleSheet(_btn_style_normal())
        self.reset_btn.clicked.connect(self.reset_config)
        button_layout.addWidget(self.reset_btn)

        self.save_btn = QPushButton("保存配置")
        self.save_btn.setStyleSheet(_btn_style_primary())
        self.save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_btn)

        main_layout.addWidget(button_row)

    def _build_path_card(self, title: str, description: str, placeholder: str,
                         is_file: bool, file_filter: str = "") -> QFrame:
        """构建路径配置卡片"""
        card = QFrame()
        card.setStyleSheet(_card_style())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-size: 14px; font-weight: 500; color: {COLOR_TEXT_TITLE}; background: transparent;"
        )
        layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setStyleSheet(
            f"font-size: 12px; color: {COLOR_TEXT_HINT}; background: transparent;"
        )
        layout.addWidget(desc_label)

        # 路径输入区域
        input_row = QWidget()
        input_row.setStyleSheet("background: transparent;")
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setStyleSheet(_input_style())
        input_layout.addWidget(line_edit, stretch=1)

        browse_btn = QPushButton("浏览...")
        browse_btn.setStyleSheet(_btn_style_normal())
        browse_btn.setFixedWidth(80)
        input_layout.addWidget(browse_btn)

        layout.addWidget(input_row)

        # 存储引用
        card.line_edit = line_edit
        card.browse_btn = browse_btn
        card.is_file = is_file
        card.file_filter = file_filter

        # 绑定浏览按钮事件
        browse_btn.clicked.connect(lambda: self._browse_path(card))

        return card

    def _build_hint_card(self) -> QFrame:
        """构建提示信息卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_PRIMARY_BG};
                border: 1px solid #91caff;
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # 提示标题
        hint_title = QLabel("💡 配置说明")
        hint_title.setStyleSheet(
            f"font-size: 13px; font-weight: 500; color: {COLOR_PRIMARY}; background: transparent; border:none;"
        )
        layout.addWidget(hint_title)

        # 提示内容
        hints = [
            "• Chrome 路径：指向 chrome.exe 可执行文件，用于启动浏览器",
            "• 用户数据目录：Chrome 的配置文件存储位置，包含登录状态、插件等",
            "• Windows 默认路径通常在: C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "• 用户数据目录通常在: C:\\Users\\<用户名>\\AppData\\Local\\Google\\Chrome\\User Data"
        ]

        for hint_text in hints:
            hint_label = QLabel(hint_text)
            hint_label.setStyleSheet(
                f"font-size: 12px; color: {COLOR_TEXT_NORMAL}; background: transparent; border:none;"
            )
            layout.addWidget(hint_label)

        return card

    def _browse_path(self, card: QFrame):
        """浏览选择路径"""
        if card.is_file:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "选择 Chrome 可执行文件",
                "",
                card.file_filter
            )
        else:
            path = QFileDialog.getExistingDirectory(
                self,
                "选择用户数据目录",
                ""
            )

        if path:
            card.line_edit.setText(path)

    def _get_current_username(self) -> str:
        """获取当前登录用户名"""
        try:
            from src.jjrj_config import JjrjConfig
            return JjrjConfig.get_username()
        except Exception:
            # 尝试从 current.json 读取
            try:
                current_file = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "user_data", "current.json"
                )
                if os.path.exists(current_file):
                    with open(current_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return data.get("username", "default")
            except Exception:
                pass
            return "default"

    def load_config(self):
        """从用户数据库加载配置"""
        try:
            from src.jjrj_config import JjrjConfig
            
            username = self._get_current_username()
            
            # 确保数据库已初始化
            JjrjConfig.init_user_database(username)
            
            # 从数据库读取配置
            chrome_path = JjrjConfig.get_setting(self.KEY_CHROME_PATH, "", username)
            user_data_path = JjrjConfig.get_setting(self.KEY_USER_DATA_PATH, "", username)
            
            self.chrome_card.line_edit.setText(chrome_path)
            self.user_data_card.line_edit.setText(user_data_path)
            
        except Exception as e:
            print(f"加载配置失败: {e}")
            # 使用默认空值

    def save_config(self):
        """保存配置到用户数据库"""
        try:
            from src.jjrj_config import JjrjConfig
            
            username = self._get_current_username()
            
            # 收集配置数据
            chrome_path = self.chrome_card.line_edit.text().strip()
            user_data_path = self.user_data_card.line_edit.text().strip()

            # 验证路径（可选，仅警告不阻止保存）
            if chrome_path and not os.path.exists(chrome_path):
                reply = QMessageBox.question(
                    self,
                    "路径不存在",
                    "Chrome 路径似乎不存在，是否继续保存？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            # 确保数据库已初始化
            JjrjConfig.init_user_database(username)
            
            # 保存到数据库
            JjrjConfig.set_setting(self.KEY_CHROME_PATH, chrome_path, username)
            JjrjConfig.set_setting(self.KEY_USER_DATA_PATH, user_data_path, username)

            QMessageBox.information(self, "保存成功", "环境配置已保存！")

        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存配置失败: {str(e)}")

    def reset_config(self):
        """重置配置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有配置吗？这将清空已设置的路径。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.chrome_card.line_edit.clear()
            self.user_data_card.line_edit.clear()

    def get_config(self) -> dict:
        """获取当前配置（从数据库读取）"""
        try:
            from src.jjrj_config import JjrjConfig
            username = self._get_current_username()
            return {
                "chrome_path": JjrjConfig.get_setting(self.KEY_CHROME_PATH, "", username),
                "user_data_path": JjrjConfig.get_setting(self.KEY_USER_DATA_PATH, "", username)
            }
        except Exception:
            return {
                "chrome_path": self.chrome_card.line_edit.text().strip(),
                "user_data_path": self.user_data_card.line_edit.text().strip()
            }

    def test_chrome_path(self) -> bool:
        """测试 Chrome 路径是否有效"""
        chrome_path = self.chrome_card.line_edit.text().strip()
        if not chrome_path:
            return False
        return os.path.exists(chrome_path) and os.path.isfile(chrome_path)
