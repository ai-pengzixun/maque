#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统
"""

import logging
from PySide6.QtCore import QObject, Signal
from datetime import datetime


class Logger(QObject):
    """日志系统类"""
    
    # 日志信号
    log_signal = Signal(str)
    
    def __init__(self):
        """初始化日志系统"""
        super().__init__()
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
    
    def _format_message(self, level: str, message: str) -> str:
        """格式化日志消息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"[{timestamp}] [{level}] {message}"
    
    def info(self, message: str):
        """信息日志"""
        logging.info(message, stacklevel=2)
        self.log_signal.emit(message)
    
    def warning(self, message: str):
        """警告日志"""
        logging.warning(message, stacklevel=2)
        self.log_signal.emit(message)
    
    def error(self, message: str):
        """错误日志"""
        logging.error(message, stacklevel=2)
        self.log_signal.emit(message)
    
    def debug(self, message: str):
        """调试日志"""
        logging.debug(message, stacklevel=2)
        self.log_signal.emit(message)