#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件下载器模块
"""

import os
import threading
from src.network.http_client import HTTPClient


class FileDownloader:
    """
    文件下载器
    """

    def __init__(self, download_dir=None):
        """
        初始化文件下载器
        
        Args:
            download_dir: 下载目录，默认为 downloads 目录
        """
        if download_dir is None:
            # 确保downloads目录存在
            self.download_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "downloads")
            os.makedirs(self.download_dir, exist_ok=True)
        else:
            self.download_dir = download_dir
        
        self.http_client = HTTPClient()
        self.downloads = {}
    
    def download_file(self, url, filename=None, callback=None):
        """
        下载文件
        
        Args:
            url: 文件URL
            filename: 保存文件名，默认为URL中的文件名
            callback: 下载进度回调函数
            
        Returns:
            下载任务ID
        """
        if not filename:
            filename = os.path.basename(url.split('?')[0])
        
        save_path = os.path.join(self.download_dir, filename)
        task_id = f"{url}_{filename}"
        
        # 创建下载线程
        def _download():
            try:
                self.downloads[task_id] = {
                    'status': 'downloading',
                    'url': url,
                    'filename': filename,
                    'path': save_path,
                    'progress': 0
                }
                
                # 下载文件
                success = self.http_client.download(url, save_path)
                
                if success:
                    self.downloads[task_id]['status'] = 'completed'
                    self.downloads[task_id]['progress'] = 100
                    if callback:
                        callback(100, save_path)
                else:
                    self.downloads[task_id]['status'] = 'failed'
            except Exception as e:
                print(f"下载文件失败: {str(e)}")
                self.downloads[task_id]['status'] = 'failed'
        
        thread = threading.Thread(target=_download)
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def get_download_status(self, task_id):
        """
        获取下载状态
        
        Args:
            task_id: 下载任务ID
            
        Returns:
            下载状态
        """
        return self.downloads.get(task_id, None)
    
    def cancel_download(self, task_id):
        """
        取消下载
        
        Args:
            task_id: 下载任务ID
            
        Returns:
            是否取消成功
        """
        if task_id in self.downloads:
            self.downloads[task_id]['status'] = 'cancelled'
            return True
        return False
    
    def get_download_dir(self):
        """
        获取下载目录
        
        Returns:
            下载目录路径
        """
        return self.download_dir
    
    def set_download_dir(self, download_dir):
        """
        设置下载目录
        
        Args:
            download_dir: 下载目录
        """
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
    
    def clear_completed(self):
        """
        清除已完成的下载任务
        """
        completed_tasks = [task_id for task_id, info in self.downloads.items() 
                         if info['status'] in ['completed', 'failed', 'cancelled']]
        for task_id in completed_tasks:
            del self.downloads[task_id]


# 全局文件下载器实例
file_downloader = FileDownloader()
