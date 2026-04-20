#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Framework 运行器
"""

import os
import sys
from typing import Optional, Dict, Any
from PySide6.QtCore import QThread, Signal
import robot
from robot.api import ExecutionResult, ResultVisitor
from src.logging_system import Logger
from src.vision_recognition import VisionRecognition


class RobotListener:
    """
    Robot Framework 监听器
    捕获每一行关键词的执行状态
    """

    def __init__(self, runner):
        """
        初始化监听器
        
        Args:
            runner: RobotRunner 实例
        """
        self.runner = runner
        self.logger = Logger()
    
    def start_suite(self, name, attrs):
        """测试套件开始"""
        self.logger.info(f"测试套件开始: {name}")
    
    def end_suite(self, name, attrs):
        """测试套件结束"""
        try:
            # 尝试获取状态，兼容不同版本的 Robot Framework
            if hasattr(attrs, 'status'):
                status = attrs.status
            else:
                status = attrs.get('status', 'UNKNOWN')
            # 直接发送信号，不通过 logger
            # 发送套件结束信号
            self.runner.suite_ended.emit(name, status)
        except Exception as e:
            self.logger.error(f"处理测试套件结束事件失败: {str(e)}")
    
    def start_test(self, name, attrs):
        """测试用例开始"""
        try:
            # 直接发送信号，不通过 logger
            # 发送测试开始信号
            self.runner.test_started.emit(name)
        except Exception as e:
            self.logger.error(f"处理测试用例开始事件失败: {str(e)}")
    
    def end_test(self, name, attrs):
        """测试用例结束"""
        try:
            # 尝试获取状态和消息，兼容不同版本的 Robot Framework
            status = 'UNKNOWN'
            message = ''
            try:
                if hasattr(attrs, 'status'):
                    status = attrs.status
                    message = getattr(attrs, 'message', '')
                else:
                    status = attrs.get('status', 'UNKNOWN')
                    message = attrs.get('message', '')
            except Exception:
                # 忽略类型转换错误
                pass
            # 直接发送信号，不通过 logger
            # 发送测试结束信号
            self.runner.test_ended.emit(name, status, message)
            # 如果测试失败，截图留证
            if status == 'FAIL':
                self.runner.capture_screenshot()
        except Exception as e:
            self.logger.error(f"处理测试用例结束事件失败: {str(e)}")
    
    def start_keyword(self, name, attrs):
        """关键词开始"""
        try:
            # 直接发送信号，不通过 logger
            # 发送关键词开始信号
            self.runner.keyword_started.emit(name)
        except Exception as e:
            self.logger.error(f"处理关键词开始事件失败: {str(e)}")
    
    def end_keyword(self, name, attrs):
        """关键词结束"""
        try:
            # 尝试获取状态和消息，兼容不同版本的 Robot Framework
            status = 'UNKNOWN'
            message = ''
            try:
                if hasattr(attrs, 'status'):
                    status = attrs.status
                    message = getattr(attrs, 'message', '')
                else:
                    status = attrs.get('status', 'UNKNOWN')
                    message = attrs.get('message', '')
            except Exception:
                # 忽略类型转换错误
                pass
            # 确保 name 是字符串
            try:
                name_str = str(name)
            except Exception:
                name_str = "unknown_keyword"
            # 直接发送信号，不通过 logger
            # 发送关键词结束信号
            self.runner.keyword_ended.emit(name_str, str(status), str(message))
        except Exception as e:
            self.logger.error(f"处理关键词结束事件失败: {str(e)}")
    
    def log_message(self, message):
        """日志消息"""
        try:
            # 尝试获取级别和消息，兼容不同版本的 Robot Framework
            if hasattr(message, 'level'):
                level = message.level
                msg = message.message
            else:
                level = message.get('level', 'INFO')
                msg = message.get('message', '')
            # 直接发送原始消息，不添加前缀
            self.runner.log_message.emit(level, msg)
        except Exception as e:
            self.logger.error(f"处理日志消息事件失败: {str(e)}")
    
    def output_file(self, path):
        """输出文件"""
        self.logger.info(f"输出文件: {path}")
    
    def summary(self, stats):
        """测试摘要"""
        self.logger.info(f"测试摘要: {stats}")
    
    def close(self):
        """关闭监听器"""
        self.logger.info("监听器关闭")


class RobotRunner(QThread):
    """
    Robot Framework 运行器
    """
    
    # 信号定义
    suite_ended = Signal(str, str)  # 套件名称, 状态
    test_started = Signal(str)  # 测试用例名称
    test_ended = Signal(str, str, str)  # 测试用例名称, 状态, 消息
    keyword_started = Signal(str)  # 关键词名称
    keyword_ended = Signal(str, str, str)  # 关键词名称, 状态, 消息
    log_message = Signal(str, str)  # 日志级别, 消息
    execution_started = Signal()  # 执行开始
    execution_ended = Signal(str)  # 执行结束, 状态
    error = Signal(str)  # 错误信息
    
    def __init__(self):
        """
        初始化 Robot Runner
        """
        super().__init__()
        self.logger = Logger()
        self.vision = VisionRecognition()
        self.robot_file = None
        self.output_dir = "output"
        self.listener = None
        self.variables = None
    
    def set_robot_file(self, robot_file: str):
        """
        设置 Robot 文件路径
        
        Args:
            robot_file: Robot 文件路径
        """
        if not os.path.exists(robot_file):
            self.logger.error(f"Robot 文件不存在: {robot_file}")
            raise FileNotFoundError(f"Robot 文件不存在: {robot_file}")
        self.robot_file = robot_file
        self.logger.info(f"设置 Robot 文件: {robot_file}")
    
    def set_output_dir(self, output_dir: str):
        """
        设置输出目录
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        self.logger.info(f"设置输出目录: {output_dir}")

    def set_variables(self, variables: Optional[Dict[str, str]]):
        """
        设置传递给 Robot Framework 的变量

        Args:
            variables: 变量字典，如 {"SEARCH_KEYWORD": "渐入佳境"}
        """
        self.variables = variables
        if variables:
            self.logger.info(f"设置 Robot 变量: {variables}")

    def capture_screenshot(self):
        """
        截图留证
        """
        try:
            import pyautogui
            import time
            from src.jjrj_config import JjrjConfig
            
            error_dir = JjrjConfig.get_error_output_dir()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(error_dir, f"screenshot_{timestamp}.png")
            pyautogui.screenshot(screenshot_path)
            self.logger.info(f"测试失败，已截图留证: {screenshot_path}")
        except Exception as e:
            self.logger.error(f"截图留证失败: {str(e)}")
    
    def run(self, variables=None):
        """
        运行 Robot Framework 测试
        
        Args:
            variables: 传递给 Robot Framework 的变量字典（可选，优先使用 self.variables）
        
        Returns:
            dict: 执行结果
        """
        if not self.robot_file:
            error_msg = "未设置 Robot 文件"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
            return {"success": False, "error": error_msg}
        
        try:
            # 确保输出目录存在
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)
            
            # 创建监听器
            self.listener = RobotListener(self)
            
            # 使用传入的 variables 或 self.variables
            vars_to_use = variables if variables is not None else self.variables
            
            # 构建变量参数（Robot Framework 格式：VAR_NAME:value）
            robot_vars = []
            if vars_to_use:
                for key, value in vars_to_use.items():
                    # Robot Framework 变量格式：VAR_NAME:value（不需要 ${}）
                    robot_vars.append(f"{key}:{value}")
                self.logger.info(f"传递变量: {robot_vars}")
            
            # 发送执行开始信号
            self.execution_started.emit()
            self.logger.info(f"开始执行 Robot 文件: {self.robot_file}")
            
            # 执行 Robot 测试
            result = robot.run(
                self.robot_file,
                outputdir=self.output_dir,
                listener=self.listener,
                output="output.xml",
                log="log.html",
                report="report.html",
                variable=robot_vars
            )
            
            # 确定执行状态
            status = "PASS" if result == 0 else "FAIL"
            self.logger.info(f"Robot 执行完成，状态: {status}")
            
            # 发送执行结束信号
            self.execution_ended.emit(status)
            
            # 如果执行失败，截图留证
            if status == "FAIL":
                self.capture_screenshot()
            
            return {"success": result == 0, "status": status}
            
        except Exception as e:
            error_msg = f"执行 Robot 测试失败: {str(e)}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
            self.capture_screenshot()
            # 发送执行结束信号
            self.execution_ended.emit("FAIL")
            return {"success": False, "error": error_msg}
    
    def stop_execution(self):
        """
        停止执行
        """
        # 注意：Robot Framework 本身不支持中途停止
        # 这里可以添加一些清理操作
        self.logger.info("停止 Robot 执行")


class RobotResultParser:
    """
    Robot Framework 结果解析器
    """

    def __init__(self, output_xml: str):
        """
        初始化结果解析器
        
        Args:
            output_xml: Robot 输出的 XML 文件路径
        """
        self.output_xml = output_xml
        self.logger = Logger()
    
    def parse(self) -> Dict[str, Any]:
        """
        解析 Robot 执行结果
        
        Returns:
            解析后的结果字典
        """
        try:
            if not os.path.exists(self.output_xml):
                self.logger.error(f"输出文件不存在: {self.output_xml}")
                return {}
            
            result = ExecutionResult(self.output_xml)
            stats = {}
            
            # 解析统计信息
            stats['total_tests'] = result.statistics.total
            stats['passed_tests'] = result.statistics.passed
            stats['failed_tests'] = result.statistics.failed
            stats['pass_rate'] = result.statistics.passed / result.statistics.total * 100 if result.statistics.total > 0 else 0
            
            # 解析测试用例
            test_cases = []
            
            class TestCaseVisitor(ResultVisitor):
                def visit_test(self, test):
                    test_cases.append({
                        'name': test.name,
                        'status': test.status,
                        'message': test.message,
                        'elapsed_time': test.elapsedtime
                    })
            
            result.visit(TestCaseVisitor())
            stats['test_cases'] = test_cases
            
            self.logger.info(f"解析 Robot 结果完成，共 {len(test_cases)} 个测试用例")
            return stats
        except Exception as e:
            self.logger.error(f"解析 Robot 结果失败: {str(e)}")
            return {}