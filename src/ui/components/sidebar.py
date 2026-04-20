#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
侧边栏组件 - Ant Design 风格
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QDialog, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor


# ── 设计 Token（与 agents.txt 保持一致）─────────────────────────────────── #
COLOR_PRIMARY        = "#1677ff"   # Ant Design Blue-6
COLOR_PRIMARY_BG     = "#e6f4ff"   # Blue-1，选中/hover 背景
COLOR_PRIMARY_BORDER = "#1677ff"   # 左侧激活指示线
COLOR_TEXT_TITLE     = "rgba(0,0,0,0.85)"
COLOR_TEXT_SECONDARY = "rgba(0,0,0,0.45)"
COLOR_TEXT_NORMAL    = "rgba(0,0,0,0.65)"
COLOR_BG_SIDEBAR     = "#ffffff"
COLOR_DIVIDER        = "#f0f0f0"
COLOR_HOVER_BG       = "#e6f4ff"
COLOR_ACTIVE_BG      = "#e6f4ff"
COLOR_LOGOUT_HOVER   = "#fff1f0"   # Red-1，退出按钮 hover

SIDEBAR_WIDTH        = 220


# ── 菜单项样式生成器 ─────────────────────────────────────────────────────── #
def _menu_item_style(active: bool, hover: bool = False) -> str:
    """生成单个菜单项的 QSS。"""
    if active:
        bg    = COLOR_ACTIVE_BG
        color = COLOR_PRIMARY
        left_border = f"border-left: 3px solid {COLOR_PRIMARY_BORDER};"
        pl    = "padding-left: 21px;"   # 24 - 3px border
    elif hover:
        bg    = COLOR_HOVER_BG
        color = COLOR_PRIMARY
        left_border = "border-left: 3px solid transparent;"
        pl    = "padding-left: 21px;"
    else:
        bg    = "transparent"
        color = COLOR_TEXT_NORMAL
        left_border = "border-left: 3px solid transparent;"
        pl    = "padding-left: 21px;"

    return f"""
        QPushButton {{
            text-align: left;
            {pl}
            padding-top: 10px;
            padding-bottom: 10px;
            padding-right: 16px;
            background-color: {bg};
            border: none;
            {left_border}
            font-size: 14px;
            color: {color};
            border-radius: 0px;
        }}
    """


def _logout_style(hover: bool = False) -> str:
    bg    = COLOR_LOGOUT_HOVER if hover else "transparent"
    color = "#ff4d4f" if hover else COLOR_TEXT_SECONDARY
    return f"""
        QPushButton {{
            text-align: left;
            padding: 10px 16px;
            background-color: {bg};
            border: none;
            border-top: 1px solid {COLOR_DIVIDER};
            font-size: 13px;
            color: {color};
            border-radius: 8px;
            font-family: 'Material Icons', 'Microsoft YaHei', sans-serif;
        }}
    """


class Sidebar(QWidget):
    """侧边栏 - Ant Design 风格"""

    # ------------------------------------------------------------------ #
    #  公共接口
    # ------------------------------------------------------------------ #
    def on_button_clicked(self, button_id):
        """按钮点击：更新选中状态"""
        for button in self.buttons:
            if button.property("button_id") == button_id:
                self.current_selected_button = button
                for btn in self.buttons:
                    self._update_button_style(btn, btn == button)
                break

    def get_button(self, button_id):
        """根据 ID 获取按钮"""
        for button in self.buttons:
            if button.property("button_id") == button_id:
                return button
        return None

    # ------------------------------------------------------------------ #
    #  初始化
    # ------------------------------------------------------------------ #
    def __init__(self):
        super().__init__()

        self.current_selected_button = None
        self.buttons = []

        # 固定侧边栏宽度
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setStyleSheet(f"background-color: {COLOR_BG_SIDEBAR};")

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._build_logo_area())
        main_layout.addWidget(self._build_divider())
        main_layout.addSpacing(8)
        main_layout.addWidget(self._build_menu())
        main_layout.addStretch()
        main_layout.addWidget(self._build_divider())
        main_layout.addWidget(self._build_user_area())
        main_layout.addWidget(self._build_logout_button())

    # ------------------------------------------------------------------ #
    #  区块构建
    # ------------------------------------------------------------------ #
    def _build_logo_area(self):
        """Logo + 应用标题区域"""
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(10)

        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources", "images", "logo_32.png"
        )
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setFixedSize(32, 32)
            layout.addWidget(logo_label)

        # 标题 + 副标题垂直排列
        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel("Maque 麻雀")
        title.setStyleSheet(
            f"font-size: 15px; font-weight: bold; color: {COLOR_TEXT_TITLE}; background: transparent;"
        )
        title_col.addWidget(title)

        subtitle = QLabel("麻雀智能体管理客户端")
        subtitle.setStyleSheet(
            f"font-size: 11px; color: {COLOR_TEXT_SECONDARY}; background: transparent;"
        )
        title_col.addWidget(subtitle)

        layout.addLayout(title_col)
        layout.addStretch()
        return w

    def _build_menu(self):
        """菜单按钮区域"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        button_configs = [
            {"name": "智能体管理", "data": "agent_management"},
            {"name": "任务列表",   "data": "task_list"},
            {"name": "环境设置",   "data": "settings"},
            {"name": "日志查看",   "data": "log_view"},
        ]

        for config in button_configs:
            btn = QPushButton(config["name"])
            btn.setFixedHeight(40)
            btn.setProperty("button_id", config["data"])
            btn.clicked.connect(
                lambda checked, d=config["data"]: self.on_button_clicked(d)
            )
            btn.enterEvent = lambda e, b=btn: self._on_button_hover(b, True)
            btn.leaveEvent = lambda e, b=btn: self._on_button_hover(b, False)
            self.buttons.append(btn)
            layout.addWidget(btn)

        # 初始化样式：第一个默认选中
        for i, btn in enumerate(self.buttons):
            active = (i == 0)
            self._update_button_style(btn, active)
            if active:
                self.current_selected_button = btn

        return container

    def _build_user_area(self):
        """底部用户信息区域 - 使用 MainWindow.current_user 中的用户信息"""
        w = QWidget()
        w.setStyleSheet(f"background-color: transparent;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # 用户头像占位（圆形色块）
        avatar = QWidget()
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet(f"""
            border-radius: 16px;
        """)
        # 尝试加载真实头像
        try:
            from src.ui.resources.resource_manager import RPixmap
            pixmap = RPixmap("user-svgrepo-com.svg", color=None)
            if not pixmap.isNull():
                icon_label = QLabel()
                icon_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                icon_label.setFixedSize(32, 32)
                layout.addWidget(icon_label)
            else:
                layout.addWidget(avatar)
        except Exception:
            layout.addWidget(avatar)

        # 用户名 + 角色 - 从 MainWindow.current_user 获取
        info_col = QVBoxLayout()
        info_col.setSpacing(1)

        # 获取当前用户信息
        username = "Admin"
        rolename = "Core Orchestrator"
        try:
            # 延迟导入避免循环依赖
            from src.main_window import MainWindow
            if MainWindow.current_user:
                username = MainWindow.current_user.get("username", "Admin")
                rolename = MainWindow.current_user.get("rolename", "Core Orchestrator")
        except Exception:
            pass

        name_label = QLabel(username)
        name_label.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {COLOR_TEXT_TITLE}; background: transparent;"
        )
        info_col.addWidget(name_label)

        role_label = QLabel(rolename)
        role_label.setStyleSheet(
            f"font-size: 11px; color: {COLOR_TEXT_SECONDARY}; background: transparent;"
        )
        info_col.addWidget(role_label)

        layout.addLayout(info_col)
        layout.addStretch()

        # 整个区域可点击
        w.mousePressEvent = lambda e: self.on_user_info_clicked()
        return w

    def _build_logout_button(self):
        """退出登录按钮"""
        from src.ui.resources.resource_manager import MATERIAL_ICONS

        self.logout_button = QPushButton(f"{MATERIAL_ICONS['logout']} 退出登录")
        self.logout_button.setFixedHeight(44)
        self.logout_button.setStyleSheet(_logout_style(hover=False))
        self.logout_button.clicked.connect(self.on_logout_clicked)
        self.logout_button.enterEvent = lambda e: (self.logout_button.setStyleSheet(_logout_style(hover=True)), self.logout_button.setCursor(Qt.CursorShape.PointingHandCursor))
        self.logout_button.leaveEvent = lambda e: (self.logout_button.setStyleSheet(_logout_style(hover=False)), self.logout_button.setCursor(Qt.CursorShape.ArrowCursor))
        self.logout_button.setCursor(Qt.CursorShape.ArrowCursor)  # 默认箭头光标
        return self.logout_button

    def _build_divider(self):
        """水平分割线"""
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {COLOR_DIVIDER};")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        return line

    # ------------------------------------------------------------------ #
    #  样式更新
    # ------------------------------------------------------------------ #
    def _update_button_style(self, button, is_active: bool):
        button.setStyleSheet(_menu_item_style(active=is_active))

    def _on_button_hover(self, button, hovered: bool):
        is_active = (button == self.current_selected_button)
        if hovered:
            button.setStyleSheet(_menu_item_style(active=is_active, hover=True))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            button.setStyleSheet(_menu_item_style(active=is_active, hover=False))
            button.setCursor(Qt.CursorShape.ArrowCursor)

    # ------------------------------------------------------------------ #
    #  状态更新（外部调用）
    # ------------------------------------------------------------------ #
    def _update_button_state(self, active_button_id):
        """从外部更新激活项"""
        for button in self.buttons:
            is_active = (button.property("button_id") == active_button_id)
            self._update_button_style(button, is_active)
            if is_active:
                self.current_selected_button = button

    # ------------------------------------------------------------------ #
    #  事件回调（供子类/外部重写）
    # ------------------------------------------------------------------ #
    def on_task_list_clicked(self):
        self._update_button_state("task_list")

    def on_settings_clicked(self):
        self._update_button_state("settings")

    def on_log_view_clicked(self):
        self._update_button_state("log_view")

    def on_agent_management_clicked(self):
        self._update_button_state("agent_management")

    def _create_custom_confirm_dialog(self, title, message):
        """创建自定义确认对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(400, 200)
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
                border-radius: 8px;
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
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(16)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: rgba(0,0,0,0.85);")
        container_layout.addWidget(title_label)
        
        # 消息
        message_label = QLabel(message)
        message_label.setStyleSheet("font-size: 14px; color: rgba(0,0,0,0.65);")
        message_label.setWordWrap(True)
        container_layout.addWidget(message_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(32)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff; color: rgba(0,0,0,0.85);
                border: 1px solid #d9d9d9; border-radius: 6px;
                padding: 0 16px; font-size: 14px;
            }
            QPushButton:hover { border-color: #1677ff; color: #1677ff; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setFixedHeight(32)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1677ff; color: #ffffff;
                border: none; border-radius: 6px;
                padding: 0 16px; font-size: 14px;
            }
            QPushButton:hover { background-color: #4096ff; }
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        container_layout.addLayout(button_layout)
        main_layout.addWidget(container)
        
        return dialog

    def on_logout_clicked(self):
        """退出登录按钮点击事件"""
        try:
            # 导入必要的模块
            import os
            import sys
            from PySide6.QtWidgets import QApplication
            
            # 显示自定义确认对话框
            dialog = self._create_custom_confirm_dialog("退出登录", "确定要退出登录吗？")
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                # 删除 current.json
                base_dir = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                )
                current_file = os.path.join(base_dir, "user_data", "current.json")
                if os.path.exists(current_file):
                    os.remove(current_file)
                    
                # 关闭主窗口
                from src.main_window import MainWindow
                for widget in QApplication.topLevelWidgets():
                    if isinstance(widget, MainWindow):
                        widget.close()
                        break
                
                # 显示登录界面
                from src.ui.components.login import LoginDialog
                login_dialog = LoginDialog()
                login_result = login_dialog.exec()
                
                # 如果登录成功，重新启动应用
                if login_result == QDialog.Accepted:
                    # 重启应用
                    QApplication.quit()
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    # 登录取消，退出程序
                    QApplication.quit()
        except Exception as e:
            print(f"退出登录失败: {e}")
            QApplication.quit()

    def on_user_info_clicked(self):
        pass
