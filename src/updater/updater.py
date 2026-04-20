#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用更新模块
实现客户端版本检查、下载和自动安装功能
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from PySide6.QtCore import QObject, Signal, QThread
from src.network.http_client import HTTPClient


# 当前客户端版本号
CURRENT_VERSION = "1.0.0"

# 更新服务器基础URL（从配置文件读取，这里是默认值）
DEFAULT_UPDATE_SERVER = "http://localhost:8000/api/client"

# 更新状态文件路径
UPDATE_STATUS_FILE = "update_status.json"

# 应用名称常量
APP_NAME = "佳境智能体管理"


class UpdateInfo:
    """更新信息类"""
    
    def __init__(self, data: Dict[str, Any]):
        self.version = data.get("version", "")
        self.download_url = data.get("download_url", "")
        self.description = data.get("description", "")
        self.is_force = data.get("is_force", False)
        self.file_size = data.get("file_size", 0)
        self.release_date = data.get("release_date", "")
        self.file_name = data.get("file_name", "")


class UpdateChecker(QThread):
    """更新检查线程"""
    
    # 信号定义
    check_completed = Signal(dict)  # 检查完成信号，传递更新信息
    check_failed = Signal(str)      # 检查失败信号，传递错误信息
    
    def __init__(self, server_url: str, current_version: str, logger=None):
        super().__init__()
        self.server_url = server_url
        self.current_version = current_version
        self.logger = logger
        self.http_client = HTTPClient()
    
    def log(self, message: str):
        """记录日志"""
        if self.logger:
            self.logger.info(f"[更新检查] {message}")
        print(f"[更新检查] {message}")
    
    def run(self):
        """执行更新检查"""
        try:
            self.log(f"开始检查更新，当前版本: {self.current_version}")
            
            # 调用检查更新接口
            url = f"{self.server_url}/check-update"
            params = {"version": self.current_version}
            
            self.log(f"请求URL: {url}")
            response = self.http_client.get(url, params=params)
            
            if response is None:
                self.log("检查更新失败: 网络请求无响应")
                self.check_failed.emit("网络请求失败，请检查网络连接")
                return
            
            # 解析响应
            if response.get("code") == 200:
                data = response.get("data", {})
                has_update = data.get("has_update", False)
                
                if has_update:
                    self.log(f"发现新版本: {data.get('version', 'unknown')}")
                    self.check_completed.emit(data)
                else:
                    self.log("当前已是最新版本")
                    self.check_completed.emit({"has_update": False})
            else:
                error_msg = response.get("msg", "未知错误")
                self.log(f"检查更新失败: {error_msg}")
                self.check_failed.emit(error_msg)
                
        except Exception as e:
            error_msg = f"检查更新异常: {str(e)}"
            self.log(error_msg)
            self.check_failed.emit(error_msg)


class UpdateDownloader(QThread):
    """更新下载线程"""
    
    # 信号定义
    download_progress = Signal(int)      # 下载进度信号 (0-100)
    download_completed = Signal(str)     # 下载完成信号，传递文件路径
    download_failed = Signal(str)        # 下载失败信号，传递错误信息
    
    def __init__(self, download_url: str, save_path: str, logger=None):
        super().__init__()
        self.download_url = download_url
        self.save_path = save_path
        self.logger = logger
        self.http_client = HTTPClient()
        self._is_cancelled = False
    
    def log(self, message: str):
        """记录日志"""
        if self.logger:
            self.logger.info(f"[更新下载] {message}")
        print(f"[更新下载] {message}")
    
    def cancel(self):
        """取消下载"""
        self._is_cancelled = True
        self.log("下载已取消")
    
    def run(self):
        """执行下载"""
        try:
            self.log(f"开始下载更新包: {self.download_url}")
            self.log(f"保存路径: {self.save_path}")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            # 使用requests进行带进度监控的下载
            import requests
            response = requests.get(self.download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._is_cancelled:
                        f.close()
                        os.remove(self.save_path)
                        self.download_failed.emit("下载已取消")
                        return
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.download_progress.emit(progress)
            
            self.log(f"下载完成: {self.save_path}")
            self.download_completed.emit(self.save_path)
            
        except Exception as e:
            error_msg = f"下载失败: {str(e)}"
            self.log(error_msg)
            # 清理未完成的文件
            if os.path.exists(self.save_path):
                os.remove(self.save_path)
            self.download_failed.emit(error_msg)


class UpdateInstaller(QObject):
    """更新安装器"""
    
    # 信号定义
    install_completed = Signal(bool, str)  # 安装完成信号 (是否成功, 消息)
    
    def __init__(self, logger=None):
        super().__init__()
        self.logger = logger
    
    def log(self, message: str):
        """记录日志"""
        if self.logger:
            self.logger.info(f"[更新安装] {message}")
        print(f"[更新安装] {message}")
    
    def install_update(self, update_package_path: str, target_dir: str) -> bool:
        """
        安装更新包
        
        Args:
            update_package_path: 更新包路径
            target_dir: 目标安装目录
            
        Returns:
            是否安装成功
        """
        try:
            self.log(f"开始安装更新包: {update_package_path}")
            self.log(f"目标目录: {target_dir}")
            
            if not os.path.exists(update_package_path):
                self.log(f"更新包不存在: {update_package_path}")
                return False
            
            # 创建临时解压目录
            temp_extract_dir = tempfile.mkdtemp(prefix="update_extract_")
            self.log(f"临时解压目录: {temp_extract_dir}")
            
            try:
                # 解压更新包
                with zipfile.ZipFile(update_package_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract_dir)
                
                self.log("更新包解压完成")
                
                # 查找解压后的可执行文件或安装脚本
                extracted_files = os.listdir(temp_extract_dir)
                self.log(f"解压内容: {extracted_files}")
                
                # 如果解压后只有一个目录，进入该目录
                if len(extracted_files) == 1:
                    subdir = os.path.join(temp_extract_dir, extracted_files[0])
                    if os.path.isdir(subdir):
                        temp_extract_dir = subdir
                
                # 查找安装程序
                installer_path = self._find_installer(temp_extract_dir)
                
                if installer_path:
                    self.log(f"找到安装程序: {installer_path}")
                    # 执行安装程序
                    self._run_installer(installer_path)
                else:
                    self.log("未找到安装程序，执行文件替换")
                    # 执行文件替换
                    self._replace_files(temp_extract_dir, target_dir)
                
                self.log("安装完成")
                return True
                
            finally:
                # 清理临时目录
                if os.path.exists(temp_extract_dir):
                    shutil.rmtree(temp_extract_dir, ignore_errors=True)
                    
        except Exception as e:
            self.log(f"安装失败: {str(e)}")
            return False
    
    def _find_installer(self, extract_dir: str) -> Optional[str]:
        """查找安装程序"""
        # 查找常见的安装程序
        installer_names = [
            "setup.exe",
            "install.exe",
            "installer.exe",
            f"{APP_NAME}.exe",
        ]
        
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower() in installer_names:
                    return os.path.join(root, file)
        
        return None
    
    def _run_installer(self, installer_path: str):
        """运行安装程序"""
        self.log(f"运行安装程序: {installer_path}")
        
        # 在Windows上使用subprocess启动安装程序
        if sys.platform == "win32":
            # 使用ShellExecute以管理员权限运行（如果需要）
            subprocess.Popen(
                [installer_path, "/SILENT"],
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            subprocess.Popen(
                [installer_path],
                shell=True
            )
    
    def _replace_files(self, source_dir: str, target_dir: str):
        """替换文件（用于绿色版更新）"""
        self.log(f"替换文件: {source_dir} -> {target_dir}")
        
        for root, dirs, files in os.walk(source_dir):
            # 计算相对路径
            rel_path = os.path.relpath(root, source_dir)
            target_path = os.path.join(target_dir, rel_path)
            
            # 确保目标目录存在
            os.makedirs(target_path, exist_ok=True)
            
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_path, file)
                
                # 备份原文件
                if os.path.exists(dst_file):
                    backup_file = f"{dst_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    shutil.copy2(dst_file, backup_file)
                
                # 复制新文件
                shutil.copy2(src_file, dst_file)
                self.log(f"已更新: {dst_file}")


class AppUpdater(QObject):
    """
    应用更新管理器
    整合检查、下载、安装功能
    """
    
    # 信号定义
    update_available = Signal(dict)      # 发现更新信号
    update_not_needed = Signal()         # 无需更新信号
    update_error = Signal(str)           # 更新错误信号
    download_progress = Signal(int)      # 下载进度信号
    download_completed = Signal(str)     # 下载完成信号
    download_failed = Signal(str)        # 下载失败信号
    install_completed = Signal(bool, str)  # 安装完成信号
    
    def __init__(self, server_url: str = None, logger=None):
        super().__init__()
        self.server_url = server_url or DEFAULT_UPDATE_SERVER
        self.logger = logger
        self.current_version = CURRENT_VERSION
        
        # 更新目录
        self.update_dir = os.path.join(self._get_app_data_dir(), "updates")
        os.makedirs(self.update_dir, exist_ok=True)
        
        # 更新状态文件
        self.status_file = os.path.join(self.update_dir, UPDATE_STATUS_FILE)
        
        # 当前更新信息
        self._current_update_info: Optional[UpdateInfo] = None
        self._downloaded_package_path: Optional[str] = None
        
        # 工作线程
        self._checker: Optional[UpdateChecker] = None
        self._downloader: Optional[UpdateDownloader] = None
    
    def log(self, message: str):
        """记录日志"""
        if self.logger:
            self.logger.info(f"[AppUpdater] {message}")
        print(f"[AppUpdater] {message}")
    
    def _get_app_data_dir(self) -> str:
        """获取应用数据目录"""
        if sys.platform == "win32":
            app_data = os.environ.get("LOCALAPPDATA", "")
            if app_data:
                return os.path.join(app_data, "JianRuJiaJing")
        
        # 回退到应用目录
        if getattr(sys, 'frozen', False):
            # 打包后的应用
            return os.path.dirname(sys.executable)
        else:
            # 开发环境
            return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    def _get_app_install_dir(self) -> str:
        """获取应用安装目录"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    def get_update_status(self) -> Dict[str, Any]:
        """获取更新状态"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"读取更新状态失败: {e}")
        
        return {
            "has_pending_update": False,
            "downloaded_version": None,
            "package_path": None,
            "download_time": None
        }
    
    def save_update_status(self, status: Dict[str, Any]):
        """保存更新状态"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存更新状态失败: {e}")
    
    def clear_update_status(self):
        """清除更新状态"""
        if os.path.exists(self.status_file):
            try:
                os.remove(self.status_file)
            except Exception as e:
                self.log(f"清除更新状态失败: {e}")
    
    def check_pending_update(self) -> Optional[Dict[str, Any]]:
        """
        检查是否有待安装的更新
        
        Returns:
            如果有待安装更新返回更新信息，否则返回None
        """
        status = self.get_update_status()
        
        if status.get("has_pending_update", False):
            package_path = status.get("package_path")
            
            if package_path and os.path.exists(package_path):
                self.log(f"发现待安装更新: {package_path}")
                return status
            else:
                self.log("待安装更新包不存在，清除状态")
                self.clear_update_status()
        
        return None
    
    def check_update(self):
        """开始检查更新"""
        self.log("启动更新检查...")
        
        # 先检查是否有待安装的更新
        pending = self.check_pending_update()
        if pending:
            self.log("有待安装的更新，跳过在线检查")
            self.update_available.emit({
                "has_update": True,
                "is_pending": True,
                "version": pending.get("downloaded_version"),
                "package_path": pending.get("package_path"),
                "description": pending.get("description", ""),
                "is_force": pending.get("is_force", False)
            })
            return
        
        # 创建并启动检查线程
        self._checker = UpdateChecker(
            self.server_url,
            self.current_version,
            self.logger
        )
        self._checker.check_completed.connect(self._on_check_completed)
        self._checker.check_failed.connect(self._on_check_failed)
        self._checker.start()
    
    def _on_check_completed(self, data: dict):
        """检查完成回调"""
        if data.get("has_update", False):
            self._current_update_info = UpdateInfo(data)
            self.update_available.emit(data)
        else:
            self.update_not_needed.emit()
    
    def _on_check_failed(self, error_msg: str):
        """检查失败回调"""
        self.update_error.emit(error_msg)
    
    def download_update(self, update_info: Dict[str, Any]) -> bool:
        """
        开始下载更新
        
        Args:
            update_info: 更新信息
            
        Returns:
            是否成功启动下载
        """
        download_url = update_info.get("download_url")
        version = update_info.get("version")
        
        if not download_url or not version:
            self.log("更新信息不完整，无法下载")
            return False
        
        # 确定保存路径
        file_name = update_info.get("file_name") or f"update_{version}.zip"
        save_path = os.path.join(self.update_dir, file_name)
        
        self.log(f"开始下载更新: {version}")
        
        # 创建并启动下载线程
        self._downloader = UpdateDownloader(download_url, save_path, self.logger)
        self._downloader.download_progress.connect(self.download_progress)
        self._downloader.download_completed.connect(self._on_download_completed)
        self._downloader.download_failed.connect(self._on_download_failed)
        self._downloader.start()
        
        return True
    
    def _on_download_completed(self, package_path: str):
        """下载完成回调"""
        self._downloaded_package_path = package_path
        
        # 保存更新状态
        if self._current_update_info:
            self.save_update_status({
                "has_pending_update": True,
                "downloaded_version": self._current_update_info.version,
                "package_path": package_path,
                "download_time": datetime.now().isoformat(),
                "description": self._current_update_info.description,
                "is_force": self._current_update_info.is_force
            })
        
        self.download_completed.emit(package_path)
    
    def _on_download_failed(self, error_msg: str):
        """下载失败回调"""
        self.download_failed.emit(error_msg)
    
    def cancel_download(self):
        """取消下载"""
        if self._downloader and self._downloader.isRunning():
            self._downloader.cancel()
    
    def install_update(self, package_path: str = None) -> bool:
        """
        安装更新
        
        Args:
            package_path: 更新包路径，如果不指定则使用已下载的包
            
        Returns:
            是否成功启动安装
        """
        if package_path is None:
            package_path = self._downloaded_package_path
        
        if not package_path or not os.path.exists(package_path):
            self.log("更新包不存在，无法安装")
            return False
        
        target_dir = self._get_app_install_dir()
        
        # 创建安装器
        installer = UpdateInstaller(self.logger)
        installer.install_completed.connect(self._on_install_completed)
        
        # 在新线程中执行安装
        import threading
        install_thread = threading.Thread(
            target=lambda: installer.install_update(package_path, target_dir)
        )
        install_thread.start()
        
        return True
    
    def _on_install_completed(self, success: bool, message: str):
        """安装完成回调"""
        if success:
            # 清除更新状态
            self.clear_update_status()
        
        self.install_completed.emit(success, message)
    
    def apply_pending_update(self) -> bool:
        """
        应用待安装的更新
        
        Returns:
            是否成功应用更新
        """
        status = self.check_pending_update()
        if not status:
            return False
        
        package_path = status.get("package_path")
        return self.install_update(package_path)


# 全局更新器实例
_updater_instance: Optional[AppUpdater] = None


def get_updater(server_url: str = None, logger=None) -> AppUpdater:
    """获取全局更新器实例"""
    global _updater_instance
    if _updater_instance is None:
        _updater_instance = AppUpdater(server_url, logger)
    return _updater_instance
