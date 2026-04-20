#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录组件 - Ant Design 风格
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog,
    QLineEdit, QCheckBox, QLabel, QPushButton, QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QColor, QPixmap
import json
import os


# ── 设计 Token（与 agents / sidebar / tasks / config 完全一致）──────────── #
COLOR_PRIMARY        = "#1677ff"
COLOR_PRIMARY_HOVER  = "#4096ff"
COLOR_PRIMARY_DARK   = "#0958d9"
COLOR_PRIMARY_BG     = "#e6f4ff"
COLOR_TEXT_TITLE     = "rgba(0,0,0,0.85)"
COLOR_TEXT_NORMAL    = "rgba(0,0,0,0.65)"
COLOR_TEXT_SECONDARY = "rgba(0,0,0,0.45)"
COLOR_BORDER         = "#d9d9d9"
COLOR_BG_CARD        = "#ffffff"
# 左侧面板背景：与主色一致，使用深蓝渐变感的深色蓝
COLOR_BG_LEFT        = "#1677ff"
COLOR_BG_LEFT_DARK   = "#0958d9"   # hover/press 时使用

# 窗口整体尺寸配置
_SHADOW_MARGIN = 16    # Dialog 四周为阴影预留的空间（px）
_CARD_W        = 900
_CARD_H        = 600
_DIALOG_W      = _CARD_W + _SHADOW_MARGIN * 2
_DIALOG_H      = _CARD_H + _SHADOW_MARGIN * 2


class LoginDialog(QDialog):
    """登录对话框 - 无边框 + 外框阴影 + 可拖动"""

    login_success = Signal(dict)   # 登录成功信号，传递用户信息

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录")
        self.setFixedSize(_DIALOG_W, _DIALOG_H)

        # ── 关键：Dialog 背景必须透明，阴影才能"透出"到 Dialog 边缘 ──
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        self._drag_pos = None
        self.init_ui()

    # ------------------------------------------------------------------ #
    #  UI 构建
    # ------------------------------------------------------------------ #
    def init_ui(self):
        # ── 主布局：四周留出 _SHADOW_MARGIN 给阴影 ──
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            _SHADOW_MARGIN, _SHADOW_MARGIN,
            _SHADOW_MARGIN, _SHADOW_MARGIN
        )
        main_layout.setSpacing(0)

        # ── 卡片容器（阴影附着在这里）──
        self.container = QFrame(self)
        self.container.setFixedSize(_CARD_W, _CARD_H)
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_CARD};
                border-radius: 8px;
            }}
        """)

        # ── 阴影效果 ──
        # 重点：阴影要加在有实体背景色的 widget 上才有效
        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 90))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        main_layout.addWidget(self.container)

        # ── 卡片内部布局（左右两栏）──
        card_layout = QHBoxLayout(self.container)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        card_layout.addWidget(self._build_left_panel(), stretch=1)
        card_layout.addWidget(self._build_right_panel(), stretch=1)

        # ── 关闭按钮：父级是 self（Dialog），使用绝对定位到右上角 ──
        # 必须挂在 self 上，不能挂在 container 上；
        # 挂在 container 上会被 QGraphicsDropShadowEffect 裁剪导致点击失效。
        # 导入 Material Icons
        from src.ui.resources.resource_manager import MATERIAL_ICONS
        self.close_btn = QPushButton(MATERIAL_ICONS["close"], self)
        self.close_btn.setFixedSize(36, 36)
        # 定位：右上角距卡片右边缘 8px、距卡片顶部 8px（均在 Dialog 坐标系）
        self.close_btn.move(
            _SHADOW_MARGIN + _CARD_W - 44,   # 卡片左起点 + 卡片宽 - 按钮宽 - 8
            _SHADOW_MARGIN + 8,
        )
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(0,0,0,0.45);
                border: none;
                border-radius: 4px;
                font-family: 'Material Icons';
                font-size: 20px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #ff4d4f;
                color: #ffffff;
            }
        """)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.on_close_clicked)
        # 必须 raise_()，否则可能被子 widget 遮住
        self.close_btn.raise_()

    # ------------------------------------------------------------------ #
    #  左侧蓝色面板
    # ------------------------------------------------------------------ #
    def _build_left_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_LEFT};
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(0)

        # Logo 行（参照 sidebar 使用图片 logo）
        logo_layout = QHBoxLayout()
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources", "images", "logo_64_w.png"
        )
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setFixedSize(32, 32)
            logo_layout.addWidget(logo_label)

        logo_text = QLabel("渐 入 佳 境")
        logo_text.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #ffffff; background: transparent; margin-left:16px;"
        )
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        layout.addLayout(logo_layout)

        layout.addSpacing(80)

        # 主标题
        title = QLabel("桌面智能，\n一站掌控。")
        title.setStyleSheet(
            "font-size: 36px; font-weight: bold; color: #ffffff; background: transparent;"
        )
        title.setWordWrap(True)
        layout.addWidget(title)

        layout.addSpacing(24)

        # 副标题
        subtitle = QLabel(
            "访问佳境智能体管理客户端。为专业的桌面工作提供\n快速、准确，节省的解决方案。"
        )
        subtitle.setStyleSheet(
            "font-size: 14px; color: rgba(255,255,255,0.75); background: transparent;"
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addStretch()

        # 底部信息行
        bottom = QHBoxLayout()
        dots = QLabel("● ● ●")
        dots.setStyleSheet(
            "font-size: 11px; color: rgba(255,255,255,0.45); background: transparent; letter-spacing: 4px;"
        )
        bottom.addWidget(dots)
        bottom.addSpacing(12)

        stats = QLabel("深受 4,000 多名智能体工程师的信赖")
        stats.setStyleSheet(
            "font-size: 12px; color: rgba(255,255,255,0.75); background: transparent;"
        )
        bottom.addWidget(stats)
        bottom.addStretch()
        layout.addLayout(bottom)

        return panel

    # ------------------------------------------------------------------ #
    #  右侧登录表单面板
    # ------------------------------------------------------------------ #
    def _build_right_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_CARD};
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(72, 72, 72, 48)
        layout.setSpacing(0)

        # 欢迎标题
        welcome = QLabel("欢迎回来")
        welcome.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: {COLOR_TEXT_TITLE}; background: transparent;"
        )
        layout.addWidget(welcome)

        layout.addSpacing(8)

        subtitle = QLabel("登录以管理您的桌面智能体")
        subtitle.setStyleSheet(
            f"font-size: 14px; color: {COLOR_TEXT_NORMAL}; background: transparent;"
        )
        layout.addWidget(subtitle)

        layout.addSpacing(40)

        # ── 用户名 ──
        layout.addWidget(self._field_label("用户名 / ID"))
        layout.addSpacing(8)
        self.username_input = self._build_line_edit("请输入用户名")
        layout.addWidget(self.username_input)

        layout.addSpacing(20)

        # ── 密码 ──
        layout.addWidget(self._field_label("密码"))
        layout.addSpacing(8)
        self.password_input = self._build_line_edit("请输入密码", echo_mode=QLineEdit.Password)
        layout.addWidget(self.password_input)

        layout.addSpacing(16)

        # ── 记住登录 + 忘记密码 ──
        options = QHBoxLayout()

        self.remember_checkbox = QCheckBox("保持登录状态")
        self.remember_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: 13px;
                color: {COLOR_TEXT_NORMAL};
                background: transparent;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 3px;
                background: #ffffff;
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLOR_PRIMARY};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLOR_PRIMARY};
                border-color: {COLOR_PRIMARY};
            }}
        """)
        options.addWidget(self.remember_checkbox)
        options.addStretch()

        forgot_btn = QPushButton("忘记密码？")
        forgot_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 13px;
                color: {COLOR_PRIMARY};
                background: transparent;
                border: none;
                padding: 0;
            }}
            QPushButton:hover {{ color: {COLOR_PRIMARY_HOVER}; text-decoration: underline; }}
        """)
        forgot_btn.setCursor(Qt.PointingHandCursor)
        options.addWidget(forgot_btn)

        layout.addLayout(options)

        layout.addSpacing(28)

        # ── 登录按钮 ──
        self.login_btn = QPushButton("登录 →")
        self.login_btn.setFixedHeight(48)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 500;
            }}
            QPushButton:hover   {{ background-color: {COLOR_PRIMARY_HOVER}; }}
            QPushButton:pressed {{ background-color: {COLOR_PRIMARY_DARK}; }}
            QPushButton:disabled {{
                background-color: #f5f5f5;
                color: rgba(0,0,0,0.25);
            }}
        """)
        self.login_btn.clicked.connect(self.on_login)
        layout.addWidget(self.login_btn)

        layout.addStretch()

        # ── 底部注册链接 ──
        bottom = QHBoxLayout()

        hint = QLabel("初次使用佳境智能体管理客户端？")
        hint.setStyleSheet(
            f"font-size: 13px; color: {COLOR_TEXT_NORMAL}; background: transparent;"
        )
        bottom.addWidget(hint)
        bottom.addStretch()

        register_btn = QPushButton("开始注册")
        register_btn.setFixedHeight(32)
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 0 16px;
                background-color: {COLOR_PRIMARY_BG};
                color: {COLOR_PRIMARY};
                border: 1px solid {COLOR_PRIMARY};
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY};
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: {COLOR_PRIMARY_DARK};
                border-color: {COLOR_PRIMARY_DARK};
                color: #ffffff;
            }}
        """)
        register_btn.clicked.connect(self.on_register_clicked)
        bottom.addWidget(register_btn)

        layout.addLayout(bottom)

        return panel

    # ── 小工具 ──────────────────────────────────────────────────────── #
    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 500; color: {COLOR_TEXT_TITLE}; background: transparent;"
        )
        return lbl

    def _build_line_edit(self, placeholder: str, echo_mode=QLineEdit.Normal) -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(44)
        edit.setEchoMode(echo_mode)
        edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: #fafafa;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 14px;
                color: {COLOR_TEXT_TITLE};
            }}
            QLineEdit:hover  {{ border-color: {COLOR_PRIMARY}; }}
            QLineEdit:focus  {{ border-color: {COLOR_PRIMARY}; background-color: #ffffff; }}
        """)
        return edit

    # ------------------------------------------------------------------ #
    #  窗口拖动（在 container 区域内拖动）
    # ------------------------------------------------------------------ #
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
            event.accept()

    # ------------------------------------------------------------------ #
    #  按钮事件
    # ------------------------------------------------------------------ #
    def on_close_clicked(self):
        self.close()

    def on_register_clicked(self):
        QDesktopServices.openUrl(QUrl("https://jrjj.toknage.com"))

    def on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username:
            self._show_error("请输入用户名")
            return
        if not password:
            self._show_error("请输入密码")
            return

        user_info = {
            "username": username,
            "nickname": username,
            "rolename": "本地管理员",
            "avatar": "",
        }

        self.save_current_user(user_info)
        self.login_success.emit(user_info)
        self.accept()

    def save_current_user(self, user_info: dict):
        try:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            user_data_dir = os.path.join(base_dir, "user_data")
            os.makedirs(user_data_dir, exist_ok=True)
            with open(os.path.join(user_data_dir, "current.json"), "w", encoding="utf-8") as f:
                json.dump(user_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户信息失败: {e}")

    def _show_error(self, message: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "提示", message)

    # 旧接口兼容
    def show_error(self, message: str):
        self._show_error(message)


# ════════════════════════════════════════════════════════════════════════════ #
#  工具函数
# ════════════════════════════════════════════════════════════════════════════ #
def check_login_status() -> tuple[bool, dict]:
    """检查本地登录状态"""
    try:
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        current_file = os.path.join(base_dir, "user_data", "current.json")
        if os.path.exists(current_file):
            with open(current_file, "r", encoding="utf-8") as f:
                user_info = json.load(f)
            if "username" in user_info:
                return True, user_info
    except Exception as e:
        print(f"检查登录状态失败: {e}")
    return False, {}


def show_login_dialog(parent=None) -> tuple[bool, dict]:
    """显示登录对话框，返回 (是否成功, 用户信息)"""
    dialog = LoginDialog(parent)
    result = dialog.exec()
    if result == QDialog.Accepted:
        _, user_info = check_login_status()
        return True, user_info
    return False, {}