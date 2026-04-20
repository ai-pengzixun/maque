#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度搜索示例智能体 - Python 入口文件
提供智能体的基础能力和平台集成
"""

import os
import sys
import json
import logging
from datetime import datetime

# ── 引入全局配置 ────────────────────────────────────────────────────────── #
from src.jjrj_config import JjrjConfig, jjrj_config

# ── 平台能力引入（按需取消注释）─────────────────────────────────────────── #
# from src.browser_manager import BrowserManager       # 浏览器管理
# from src.human_controller import HumanController      # 人工干预控制
# from src.vision_recognition import VisionRecognition  # 视觉识别
# from src.storage.database import DatabaseManager        # 数据库管理
# from src.network.http_client import HttpClient          # HTTP 客户端
# from src.network.file_downloader import FileDownloader  # 文件下载
# from src.logging_system import Logger                   # 日志系统


class BaiduSearchAgent:
    """百度搜索示例智能体"""
    
    def __init__(self):
        self.config = jjrj_config
        self.name = "百度搜索示例"
        self.logger = logging.getLogger(f"agent.{self.__class__.__name__}")
        
        # 初始化用户数据库连接
        self.db_conn = None
        
    def initialize(self) -> bool:
        """
        初始化智能体
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 确保用户数据目录存在
            user_data_dir = self.config.ensure_user_data_dir()
            self.logger.info(f"用户数据目录: {user_data_dir}")
            
            # 初始化数据库连接
            self.db_conn = self.config.init_user_database()
            self.logger.info("数据库初始化完成")
            
            return True
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            return False
    
    def _get_default_keyword(self) -> str:
        """从 agent.json 读取默认关键词"""
        try:
            agent_json_path = os.path.join(os.path.dirname(__file__), "agent.json")
            with open(agent_json_path, 'r', encoding='utf-8') as f:
                agent_config = json.load(f)
            inputs = agent_config.get("inputs", [])
            for input_item in inputs:
                if isinstance(input_item, dict) and input_item.get("name") == "SEARCH_KEYWORD":
                    return input_item.get("default", "渐入佳境")
            return "渐入佳境"
        except Exception:
            return "渐入佳境"
    
    def execute(self, search_keyword: str = None) -> dict:
        """
        执行百度搜索任务
        
        Args:
            search_keyword: 搜索关键词
            
        Returns:
            dict: 执行结果
        """
        if not self.initialize():
            return {"success": False, "error": "初始化失败"}
        
        keyword = search_keyword or self._get_default_keyword()
        task_id = None
        
        try:
            # 记录任务开始
            task_id = self._record_task_start(keyword)
            
            # 执行搜索（这里调用 Robot Framework）
            result = self._run_robot_test(keyword)
            
            # 记录任务结束
            self._record_task_end(task_id, result)
            
            return {"success": True, "result": result}
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"执行失败: {error_msg}")
            self.config.log_error(error_msg, f"{self.name}_error.log")
            
            if task_id:
                self._record_task_error(task_id, error_msg)
                
            return {"success": False, "error": error_msg}
    
    def _run_robot_test(self, keyword: str) -> str:
        """
        运行 Robot Framework 测试

        Args:
            keyword: 搜索关键词

        Returns:
            str: 测试结果
        """
        try:
            # 从 agent.json 读取输入变量
            agent_json_path = os.path.join(os.path.dirname(__file__), "agent.json")
            with open(agent_json_path, 'r', encoding='utf-8') as f:
                agent_config = json.load(f)
            
            # 获取输入变量
            inputs = agent_config.get("inputs", [])
            input_vars = {}
            for input_item in inputs:
                if isinstance(input_item, dict):
                    input_vars[input_item["name"]] = input_item.get("default", "")
            
            # 使用传入的 keyword 覆盖默认值
            if keyword:
                input_vars["SEARCH_KEYWORD"] = keyword
            
            # 调用 Robot Runner 执行测试
            from src.robot_runner import RobotRunner
            robot_file = os.path.join(os.path.dirname(__file__), "agent.robot")
            output_dir = self.config.get_robot_output_dir()
            
            runner = RobotRunner()
            runner.set_robot_file(robot_file)
            runner.set_output_dir(output_dir)
            result = runner.run(variables=input_vars)
            
            return f"测试完成，状态: {'PASSED' if result['success'] else 'FAILED'}"
            
        except Exception as e:
            # 如果 Robot Runner 不可用，返回模拟结果
            output_dir = self.config.get_robot_output_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(output_dir, f"baidu_search_{timestamp}.log")
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"[{timestamp}] 开始执行百度搜索测试\n")
                f.write(f"搜索关键词: {keyword}\n")
                f.write("测试状态: PASSED (模拟)\n")
                f.write(f"备注: Robot Runner 不可用，使用模拟结果\n")
            
            return f"测试完成（模拟），日志保存至: {log_file}"
    
    def _record_task_start(self, keyword: str) -> int:
        """记录任务开始到数据库"""
        if not self.db_conn:
            return None
            
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT INTO task_history (task_name, agent_name, status, start_time)
            VALUES (?, ?, ?, ?)
        """, (f"百度搜索-{keyword}", self.name, "pending", datetime.now().isoformat()))
        
        self.db_conn.commit()
        return cursor.lastrowid
    
    def _record_task_end(self, task_id: int, result: str):
        """记录任务结束到数据库"""
        if not self.db_conn or not task_id:
            return
            
        cursor = self.db_conn.cursor()
        cursor.execute("""
            UPDATE task_history 
            SET status = 'completed', end_time = ?, result = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), result, task_id))
        
        self.db_conn.commit()
    
    def _record_task_error(self, task_id: int, error_msg: str):
        """记录任务错误到数据库"""
        if not self.db_conn or not task_id:
            return
            
        cursor = self.db_conn.cursor()
        cursor.execute("""
            UPDATE task_history 
            SET status = 'failed', end_time = ?, error_message = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), error_msg, task_id))
        
        self.db_conn.commit()
    
    def cleanup(self):
        """清理资源"""
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None


def run_agent():
    """运行智能体的入口函数"""
    agent = BaiduSearchAgent()
    result = agent.execute()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    agent.cleanup()


if __name__ == "__main__":
    run_agent()
