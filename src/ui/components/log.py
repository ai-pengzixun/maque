#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志查看器组件 - Ant Design 风格
"""

from PySide6.QtWidgets import QPlainTextEdit


class LogViewer(QPlainTextEdit):
    """日志查看器"""

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #ffffff;
                color: #333333;
                font-family: "Consolas", "JetBrains Mono", "Fira Code", monospace;
                font-size: 13px;
                border: 1px solid #e1e8f0;
                border-radius: 6px;
                padding: 8px;
            }
        """)

    def append_log(self, message: str):
        self.appendPlainText(message)
