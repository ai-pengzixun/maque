#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP客户端模块
"""

import requests
import json
from typing import Dict, Any, Optional


class HTTPClient:
    """
    HTTP客户端
    """

    def __init__(self, base_url=None, timeout=30):
        """
        初始化HTTP客户端
        
        Args:
            base_url: 基础URL
            timeout: 超时时间（秒）
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RPA Client/1.0'
        })
    
    def get(self, url, params=None, headers=None):
        """
        发送GET请求
        
        Args:
            url: 请求URL
            params: 请求参数
            headers: 请求头
            
        Returns:
            响应数据
        """
        try:
            if self.base_url and not url.startswith('http'):
                url = self.base_url + url
            
            response = self.session.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"GET请求失败: {str(e)}")
            return None
    
    def post(self, url, data=None, json=None, headers=None):
        """
        发送POST请求
        
        Args:
            url: 请求URL
            data: 表单数据
            json: JSON数据
            headers: 请求头
            
        Returns:
            响应数据
        """
        try:
            if self.base_url and not url.startswith('http'):
                url = self.base_url + url
            
            response = self.session.post(
                url, 
                data=data, 
                json=json, 
                headers=headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"POST请求失败: {str(e)}")
            return None
    
    def put(self, url, data=None, json=None, headers=None):
        """
        发送PUT请求
        
        Args:
            url: 请求URL
            data: 表单数据
            json: JSON数据
            headers: 请求头
            
        Returns:
            响应数据
        """
        try:
            if self.base_url and not url.startswith('http'):
                url = self.base_url + url
            
            response = self.session.put(
                url, 
                data=data, 
                json=json, 
                headers=headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"PUT请求失败: {str(e)}")
            return None
    
    def delete(self, url, headers=None):
        """
        发送DELETE请求
        
        Args:
            url: 请求URL
            headers: 请求头
            
        Returns:
            响应数据
        """
        try:
            if self.base_url and not url.startswith('http'):
                url = self.base_url + url
            
            response = self.session.delete(
                url, 
                headers=headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"DELETE请求失败: {str(e)}")
            return None
    
    def download(self, url, save_path):
        """
        下载文件
        
        Args:
            url: 文件URL
            save_path: 保存路径
            
        Returns:
            是否下载成功
        """
        try:
            if self.base_url and not url.startswith('http'):
                url = self.base_url + url
            
            response = self.session.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
        except Exception as e:
            print(f"文件下载失败: {str(e)}")
            return False
    
    def set_header(self, key, value):
        """
        设置请求头
        
        Args:
            key: 头字段名
            value: 头字段值
        """
        self.session.headers.update({key: value})
    
    def set_auth(self, username, password):
        """
        设置基本认证
        
        Args:
            username: 用户名
            password: 密码
        """
        self.session.auth = (username, password)
    
    def set_token(self, token, prefix='Bearer'):
        """
        设置令牌认证
        
        Args:
            token: 令牌
            prefix: 令牌前缀
        """
        self.set_header('Authorization', f'{prefix} {token}')
    
    def close(self):
        """
        关闭会话
        """
        self.session.close()


# 全局HTTP客户端实例
http_client = HTTPClient()
