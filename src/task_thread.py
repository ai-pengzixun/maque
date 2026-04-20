#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务线程
"""

import time
import random
from PySide6.QtCore import QThread
from src.logging_system import Logger


class TestTaskThread(QThread):
    """测试任务线程"""

    def __init__(self):
        """初始化测试任务线程"""
        super().__init__()
        self.logger = Logger()
        self.running = True
    
    def run(self):
        """运行测试任务"""
        try:
            for i in range(10):
                if not self.running:
                    break
                
                # 模拟任务执行
                task_message = f"执行任务步骤 {i+1}"
                self.logger.info(task_message)
                
                # 随机延迟，模拟人类操作
                delay = random.uniform(0.8, 1.2)
                time.sleep(delay)
            
            self.logger.info("测试任务完成")
        except Exception as e:
            self.logger.error(f"任务执行出错: {str(e)}")
    
    def stop(self):
        """停止任务"""
        self.running = False