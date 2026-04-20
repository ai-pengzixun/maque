#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite数据库管理模块
"""

import sqlite3
import os
from datetime import datetime


class DatabaseManager:
    """
    SQLite数据库管理器
    """

    def __init__(self, db_file=None):
        """
        初始化数据库管理器
        
        Args:
            db_file: 数据库文件路径，默认为 data/rpa.db
        """
        if db_file is None:
            # 确保data目录存在
            os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data"), exist_ok=True)
            self.db_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "rpa.db")
        else:
            self.db_file = db_file
        
        self.conn = None
        self.cursor = None
        self._init_db()
    
    def _init_db(self):
        """
        初始化数据库，创建必要的表
        """
        try:
            self.connect()
            # 创建视频评论表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS video_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_url TEXT NOT NULL,
                    comment_content TEXT NOT NULL,
                    status TEXT DEFAULT '待评论',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建任务表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建智能体表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'ready',
                    path TEXT NOT NULL,
                    config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            self.close()
        except Exception as e:
            print(f"初始化数据库失败: {str(e)}")
            if self.conn:
                self.conn.rollback()
            self.close()
    
    def connect(self):
        """
        连接到数据库
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"连接数据库失败: {str(e)}")
            return False
    
    def close(self):
        """
        关闭数据库连接
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            self.cursor = None
            self.conn = None
        except Exception as e:
            print(f"关闭数据库连接失败: {str(e)}")
    
    def execute(self, query, params=None):
        """
        执行SQL语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            执行结果
        """
        try:
            if not self.conn:
                self.connect()
            
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"执行SQL失败: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def fetch_all(self, query, params=None):
        """
        获取所有查询结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            if not self.conn:
                self.connect()
            
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            return self.cursor.fetchall()
        except Exception as e:
            print(f"查询数据失败: {str(e)}")
            return []
    
    def fetch_one(self, query, params=None):
        """
        获取单条查询结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果
        """
        try:
            if not self.conn:
                self.connect()
            
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            return self.cursor.fetchone()
        except Exception as e:
            print(f"查询数据失败: {str(e)}")
            return None
    
    def insert(self, table, data):
        """
        插入数据
        
        Args:
            table: 表名
            data: 数据字典
            
        Returns:
            是否插入成功
        """
        try:
            keys = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = tuple(data.values())
            
            query = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
            return self.execute(query, values)
        except Exception as e:
            print(f"插入数据失败: {str(e)}")
            return False
    
    def update(self, table, data, condition):
        """
        更新数据
        
        Args:
            table: 表名
            data: 数据字典
            condition: 更新条件
            
        Returns:
            是否更新成功
        """
        try:
            set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
            values = tuple(data.values())
            
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
            return self.execute(query, values)
        except Exception as e:
            print(f"更新数据失败: {str(e)}")
            return False
    
    def delete(self, table, condition):
        """
        删除数据
        
        Args:
            table: 表名
            condition: 删除条件
            
        Returns:
            是否删除成功
        """
        try:
            query = f"DELETE FROM {table} WHERE {condition}"
            return self.execute(query)
        except Exception as e:
            print(f"删除数据失败: {str(e)}")
            return False
    
    def get_last_insert_id(self):
        """
        获取最后插入的ID
        
        Returns:
            最后插入的ID
        """
        try:
            if not self.conn:
                self.connect()
            
            self.cursor.execute("SELECT last_insert_rowid()")
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"获取最后插入ID失败: {str(e)}")
            return None


# 全局数据库管理器实例
db_manager = DatabaseManager()
