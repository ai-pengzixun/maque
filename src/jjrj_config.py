#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JianRuJiaJing 全局配置类
提供规范化的路径和配置变量供所有 agent 使用
"""

import os
import sqlite3
import json
from pathlib import Path


class JjrjConfig:
    """全局配置类 - 提供规范化的路径和配置变量"""
    
    # ── 类变量：项目根目录 ────────────────────────────────────────────────── #
    _base_dir = None
    _current_user = None
    
    @classmethod
    def get_base_dir(cls) -> str:
        """获取项目根目录"""
        if cls._base_dir is None:
            cls._base_dir = str(Path(__file__).parent.parent)
        return cls._base_dir
    
    @classmethod
    def set_current_user(cls, user_info: dict):
        """设置当前用户信息"""
        cls._current_user = user_info
    
    @classmethod
    def get_current_user(cls) -> dict:
        """获取当前用户信息"""
        return cls._current_user or {}
    
    @classmethod
    def get_username(cls) -> str:
        """获取当前用户名"""
        return cls.get_current_user().get("username", "default")
    
    # ── 规范化路径定义 ────────────────────────────────────────────────────── #
    
    @classmethod
    def get_user_data_root(cls) -> str:
        """
        获取用户数据根目录
        
        Returns:
            str: user_data 目录路径 (如: D:/.../user_data)
        """
        return os.path.join(cls.get_base_dir(), "user_data")
    
    @classmethod
    def get_user_data_dir(cls, username: str = None) -> str:
        """
        获取特定用户的用户数据目录
        
        Args:
            username: 用户名（可选，默认使用当前登录用户）
            
        Returns:
            str: 用户数据目录路径 (如: D:/.../user_data_localuser)
        """
        username = username or cls.get_username()
        return os.path.join(cls.get_user_data_root(), f"user_data_{username}")
    
    @classmethod
    def ensure_user_data_dir(cls, username: str = None) -> str:
        """
        确保用户数据目录存在，不存在则创建
        
        Args:
            username: 用户名
            
        Returns:
            str: 用户数据目录路径
        """
        user_data_dir = cls.get_user_data_dir(username)
        os.makedirs(user_data_dir, exist_ok=True)
        return user_data_dir
    
    @classmethod
    def get_error_output_dir(cls) -> str:
        """
        获取错误输出目录
        
        Returns:
            str: errors 目录路径 (如: D:/.../data/errors)
        """
        error_dir = os.path.join(cls.get_base_dir(), "data", "errors")
        os.makedirs(error_dir, exist_ok=True)
        return error_dir
    
    @classmethod
    def get_robot_output_dir(cls) -> str:
        """
        获取 Robot 脚本输出目录
        
        Returns:
            str: robot_output 目录路径 (如: D:/.../data/robot_output)
        """
        output_dir = os.path.join(cls.get_base_dir(), "data", "robot_output")
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    @classmethod
    def get_task_history_dir(cls) -> str:
        """
        获取任务执行历史目录
        
        Returns:
            str: task_history 目录路径 (如: D:/.../data/task_history)
        """
        history_dir = os.path.join(cls.get_base_dir(), "data", "task_history")
        os.makedirs(history_dir, exist_ok=True)
        return history_dir
    
    @classmethod
    def get_config_dir(cls) -> str:
        """
        获取配置文件目录
        
        Returns:
            str: config 目录路径
        """
        config_dir = os.path.join(cls.get_base_dir(), "config")
        os.makedirs(config_dir, exist_ok=True)
        return config_dir
    
    @classmethod
    def get_agents_dir(cls) -> str:
        """
        获取智能体目录
        
        Returns:
            str: agents 目录路径
        """
        return os.path.join(cls.get_base_dir(), "agents")
    
    # ── 数据库操作 ────────────────────────────────────────────────────────── #
    
    @classmethod
    def get_user_db_path(cls, username: str = None) -> str:
        """
        获取用户数据库路径
        
        Args:
            username: 用户名
            
        Returns:
            str: 数据库文件路径 (如: D:/.../user_data_localuser/localuser.db)
        """
        username = username or cls.get_username()
        user_data_dir = cls.ensure_user_data_dir(username)
        return os.path.join(user_data_dir, f"{username}.db")
    
    @classmethod
    def init_user_database(cls, username: str = None) -> sqlite3.Connection:
        """
        初始化用户数据库并返回连接
        
        Args:
            username: 用户名
            
        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        db_path = cls.get_user_db_path(username)
        
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                start_time TEXT,
                end_time TEXT,
                duration REAL,
                result TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                level TEXT,
                message TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(task_id) REFERENCES task_history(id)
            )
        """)
        
        # 创建设置表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        return conn
    
    @classmethod
    def get_setting(cls, key: str, default: str = None, username: str = None) -> str:
        """
        获取设置值
        
        Args:
            key: 设置键名
            default: 默认值
            username: 用户名（可选，默认使用当前登录用户）
            
        Returns:
            str: 设置值
        """
        try:
            db_path = cls.get_user_db_path(username)
            if not os.path.exists(db_path):
                return default
            
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else default
        except Exception:
            return default
    
    @classmethod
    def set_setting(cls, key: str, value: str, username: str = None):
        """
        设置配置项
        
        Args:
            key: 设置键名
            value: 设置值
            username: 用户名（可选，默认使用当前登录用户）
        """
        db_path = cls.get_user_db_path(username)
        conn = sqlite3.connect(db_path)
        
        from datetime import datetime
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.execute("""
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (key, value, updated_at))
        
        conn.commit()
        conn.close()
    
    @classmethod
    def get_all_settings(cls, username: str = None) -> dict:
        """
        获取所有设置
        
        Args:
            username: 用户名（可选，默认使用当前登录用户）
            
        Returns:
            dict: 所有设置的键值对
        """
        try:
            db_path = cls.get_user_db_path(username)
            if not os.path.exists(db_path):
                return {}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT key, value FROM settings")
            rows = cursor.fetchall()
            conn.close()
            
            return {row[0]: row[1] for row in rows}
        except Exception:
            return {}
    
    # ── 环境配置（从数据库读取）────────────────────────────────────────────── #
    
    ENV_KEY_CHROME_PATH = "chrome_path"
    ENV_KEY_USER_DATA_PATH = "user_data_path"
    
    @classmethod
    def is_env_configured(cls, username: str = None) -> bool:
        """
        检查环境是否已配置完成
        
        Args:
            username: 用户名（可选，默认使用当前登录用户）
            
        Returns:
            bool: 环境是否已配置
        """
        try:
            chrome_path = cls.get_setting(cls.ENV_KEY_CHROME_PATH, "", username)
            return bool(chrome_path.strip())
        except Exception:
            return False
    
    @classmethod
    def get_env_config(cls, username: str = None) -> dict:
        """
        获取环境配置
        
        Args:
            username: 用户名（可选，默认使用当前登录用户）
            
        Returns:
            dict: 环境配置字典
        """
        return {
            "chrome_path": cls.get_setting(cls.ENV_KEY_CHROME_PATH, "", username),
            "user_data_path": cls.get_setting(cls.ENV_KEY_USER_DATA_PATH, "", username)
        }
    
    @classmethod
    def set_env_config(cls, chrome_path: str, user_data_path: str = "", username: str = None):
        """
        设置环境配置
        
        Args:
            chrome_path: Chrome 浏览器路径
            user_data_path: 用户数据目录路径
            username: 用户名（可选，默认使用当前登录用户）
        """
        cls.set_setting(cls.ENV_KEY_CHROME_PATH, chrome_path, username)
        cls.set_setting(cls.ENV_KEY_USER_DATA_PATH, user_data_path, username)
    
    # ── 便捷方法 ────────────────────────────────────────────────────────── #
    
    @classmethod
    def log_error(cls, error_msg: str, filename: str = "error.log"):
        """
        记录错误到错误输出目录
        
        Args:
            error_msg: 错误消息
            filename: 日志文件名
        """
        error_dir = cls.get_error_output_dir()
        log_path = os.path.join(error_dir, filename)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {error_msg}\n")


# 创建全局单例实例
jjrj_config = JjrjConfig()
