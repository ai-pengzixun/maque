#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主显示区组件 - Ant Design 风格
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QWidget
)


class MainContent(QWidget):
    """主显示区：负责在各子页面之间切换"""

    def __init__(self):
        super().__init__()

        # 子页面
        from src.ui.components.log import LogViewer
        self.log_viewer = LogViewer()

        from src.ui.components.agents import AgentManagement
        self.agent_management_ui = AgentManagement()

        from src.ui.components.tasks import TasksUI
        self.tasks_ui = TasksUI()

        from src.ui.components.env_settings import EnvSettings
        self.env_settings = EnvSettings()

        # 容器布局
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # 默认显示日志
        self._layout.addWidget(self.log_viewer)

    # ------------------------------------------------------------------ #
    def _switch_to(self, target: QWidget):
        """隐藏所有子页面，显示 target"""
        all_widgets = [self.log_viewer, self.tasks_ui, self.agent_management_ui, self.env_settings]
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().hide()
        for w in all_widgets:
            if w is not target and w.parent() is not self:
                pass  # 未加入过布局，不需要额外处理
        self._layout.addWidget(target)
        target.show()

    def show_log_view(self):
        self._switch_to(self.log_viewer)

    def show_task_list(self):
        self._switch_to(self.tasks_ui)

    def show_agent_management(self):
        self._switch_to(self.agent_management_ui)

    def show_env_settings(self):
        self._switch_to(self.env_settings)

    def add_widget(self, widget: QWidget):
        self._layout.addWidget(widget)
