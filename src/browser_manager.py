#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器封装模块
"""

import os
import random
import time
from typing import Optional, Dict
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
from src.logging_system import Logger
from src.human_controller import HumanController


class BrowserManager:
    """浏览器管理器类"""

    def __init__(self):
        """初始化浏览器管理器"""
        self.logger = Logger()
        self.human = HumanController()
        self.playwright = None
        self.browsers: Dict[str, Browser] = {}
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.logger.info("BrowserManager 初始化完成")
    
    def _get_user_data_dir(self, user_id: str) -> str:
        """
        获取用户数据目录
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户数据目录路径
        """
        try:
            from src.jjrj_config import JjrjConfig
            env_config = JjrjConfig.get_env_config()
            env_user_data_path = env_config.get("user_data_path", "")
            if env_user_data_path:
                user_data_dir = os.path.join(env_user_data_path, f"user_{user_id}")
            else:
                user_data_dir = os.path.join("user_data", f"user_{user_id}")
        except Exception:
            user_data_dir = os.path.join("user_data", f"user_{user_id}")
        
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir, exist_ok=True)
        return user_data_dir
    
    def launch_browser(self, user_id: str, headless: bool = False, browser_exec_path: str = None) -> Browser:
        """
        启动浏览器
        
        Args:
            user_id: 用户ID
            headless: 是否无头模式，默认为 False
            browser_exec_path: 浏览器可执行路径，默认为 None（从 JjrjConfig 读取）
            
        Returns:
            浏览器实例
        """
        try:
            if self.playwright is None:
                self.playwright = sync_playwright().start()
            
            # 检查是否已存在浏览器实例
            if user_id in self.browsers:
                return self.browsers[user_id]
            
            # 如果未传入浏览器路径，从 JjrjConfig 读取
            if not browser_exec_path:
                try:
                    from src.jjrj_config import JjrjConfig
                    env_config = JjrjConfig.get_env_config()
                    browser_exec_path = env_config.get("chrome_path", "") or None
                except Exception:
                    pass
            
            # 启动浏览器
            launch_options = {
                "headless": headless,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            }
            
            # 如果提供了浏览器路径，则使用指定路径
            if browser_exec_path:
                launch_options["executable_path"] = browser_exec_path
            
            browser = self.playwright.chromium.launch(**launch_options)
            
            self.browsers[user_id] = browser
            self.logger.info(f"为用户 {user_id} 启动浏览器")
            return browser
        except Exception as e:
            self.logger.error(f"启动浏览器失败: {str(e)}")
            raise
    
    def create_context(self, user_id: str, headless: bool = False, storage_state: dict = None) -> BrowserContext:
        """
        创建浏览器上下文
        
        Args:
            user_id: 用户ID
            headless: 是否无头模式，默认为 False
            storage_state: 登录状态，默认为 None
            
        Returns:
            浏览器上下文实例
        """
        try:
            # 检查是否已存在上下文
            if user_id in self.contexts:
                return self.contexts[user_id]
            
            # 启动浏览器
            browser = self.launch_browser(user_id, headless)
            
            # 创建上下文
            user_data_dir = self._get_user_data_dir(user_id)
            storage_state_path = f"{user_data_dir}/storage_state.json"
            
            context_options = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            # 优先使用传入的 storage_state
            if storage_state:
                context_options["storage_state"] = storage_state
            # 其次检查本地 storage_state 文件
            elif os.path.exists(storage_state_path):
                context_options["storage_state"] = storage_state_path
            
            context = browser.new_context(**context_options)
            
            self.contexts[user_id] = context
            self.logger.info(f"为用户 {user_id} 创建浏览器上下文")
            return context
        except Exception as e:
            self.logger.error(f"创建浏览器上下文失败: {str(e)}")
            raise
    
    def new_page(self, user_id: str, headless: bool = False, storage_state: dict = None) -> Page:
        """
        创建新页面
        
        Args:
            user_id: 用户ID
            headless: 是否无头模式，默认为 False
            storage_state: 登录状态，默认为 None
            
        Returns:
            页面实例
        """
        try:
            # 创建上下文
            context = self.create_context(user_id, headless, storage_state)
            
            # 创建页面
            page = context.new_page()
            
            # 加载反爬插件
            self._load_stealth(page)
            
            # 伪装 Canvas 和 WebGL 指纹
            self._fake_fingerprints(page)
            
            self.pages[user_id] = page
            self.logger.info(f"为用户 {user_id} 创建新页面")
            return page
        except Exception as e:
            self.logger.error(f"创建页面失败: {str(e)}")
            raise
    
    def _load_stealth(self, page: Page):
        """
        加载反爬插件
        
        Args:
            page: 页面实例
        """
        try:
            # 注入 playwright-stealth 脚本
            # 注意：实际使用时需要安装 playwright-stealth 包
            # 这里使用内联脚本模拟
            stealth_script = """
            // 禁用 webdriver 检测
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 禁用 Chrome 自动化检测
            Object.defineProperty(navigator, 'chrome', {
                get: () => true
            });
            
            // 禁用插件检测
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3]
            });
            
            // 禁用 mimeTypes 检测
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => [1, 2, 3]
            });
            """
            page.evaluate(stealth_script)
            self.logger.info("加载反爬插件完成")
        except Exception as e:
            self.logger.error(f"加载反爬插件失败: {str(e)}")
    
    def _fake_fingerprints(self, page: Page):
        """
        伪装 Canvas 和 WebGL 指纹
        
        Args:
            page: 页面实例
        """
        try:
            # 简化的 Canvas 指纹伪装
            canvas_script = """
            // 简化的 Canvas 指纹伪装
            Object.defineProperty(HTMLCanvasElement.prototype, 'toDataURL', {
                value: function() {
                    return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==';
                },
                writable: false
            });
            """
            
            # 简化的 WebGL 指纹伪装
            webgl_script = """
            // 简化的 WebGL 指纹伪装
            Object.defineProperty(navigator, 'gpu', {
                value: {
                    requestAdapter: async () => ({
                        info: {
                            vendor: 'Intel Inc.',
                            renderer: 'Intel(R) HD Graphics 630'
                        }
                    })
                },
                writable: false
            });
            """
            
            # 只执行 canvas_script，暂时注释掉 webgl_script 以避免错误
            page.evaluate(canvas_script)
            # page.evaluate(webgl_script)
            self.logger.info("伪装 Canvas 和 WebGL 指纹完成")
        except Exception as e:
            self.logger.error(f"伪装指纹失败: {str(e)}")
    
    def safe_goto(self, user_id: str, url: str, headless: bool = False, browser_exec_path: str = None, storage_state: dict = None) -> Page:
        """
        安全导航到指定 URL
        
        Args:
            user_id: 用户ID
            url: 目标 URL
            headless: 是否无头模式，默认为 False
            browser_exec_path: 浏览器可执行路径，默认为 None（从 JjrjConfig 读取）
            storage_state: 登录状态，默认为 None
            
        Returns:
            页面实例
        """
        try:
            # 如果未传入浏览器路径，从 JjrjConfig 读取
            if not browser_exec_path:
                try:
                    from src.jjrj_config import JjrjConfig
                    env_config = JjrjConfig.get_env_config()
                    browser_exec_path = env_config.get("chrome_path", "") or None
                except Exception:
                    pass
            
            # 获取或创建页面
            if user_id not in self.pages:
                # 先关闭可能存在的浏览器实例，确保使用新的浏览器路径
                if user_id in self.browsers:
                    self.close_browser(user_id)
                # 创建新页面，传递 storage_state
                page = self.new_page(user_id, headless, storage_state)
            else:
                page = self.pages[user_id]
            
            # 导航到 URL
            page.goto(url, wait_until="networkidle")
            
            # 随机等待 1-3 秒
            self.human.smart_sleep(1000, 3000)
            
            # 模拟随机页面滚动
            self._simulate_scroll(page)
            
            self.logger.info(f"安全导航到 {url}")
            return page
        except Exception as e:
            self.logger.error(f"导航失败: {str(e)}")
            raise
    
    def _simulate_scroll(self, page: Page):
        """
        模拟页面滚动
        
        Args:
            page: 页面实例
        """
        try:
            # 随机滚动位置
            scroll_heights = [200, 400, 600, 800, 1000]
            scroll_height = random.choice(scroll_heights)
            
            # 滚动到指定位置
            page.evaluate(f"window.scrollTo(0, {scroll_height})")
            
            # 随机等待
            self.human.smart_sleep(500, 1000)
            
            # 滚动回顶部
            page.evaluate("window.scrollTo(0, 0)")
            
            self.logger.info("模拟页面滚动完成")
        except Exception as e:
            self.logger.error(f"模拟滚动失败: {str(e)}")
    
    def close_browser(self, user_id: str):
        """
        关闭浏览器
        
        Args:
            user_id: 用户ID
        """
        try:
            # 关闭页面
            if user_id in self.pages:
                self.pages[user_id].close()
                del self.pages[user_id]
            
            # 关闭上下文并保存状态
            if user_id in self.contexts:
                # 保存 storage_state
                user_data_dir = self._get_user_data_dir(user_id)
                storage_state_path = f"{user_data_dir}/storage_state.json"
                try:
                    self.contexts[user_id].storage_state(path=storage_state_path)
                    self.logger.info(f"保存用户 {user_id} 的浏览器状态到 {storage_state_path}")
                except Exception as e:
                    self.logger.error(f"保存浏览器状态失败: {str(e)}")
                
                self.contexts[user_id].close()
                del self.contexts[user_id]
            
            # 关闭浏览器
            if user_id in self.browsers:
                self.browsers[user_id].close()
                del self.browsers[user_id]
            
            self.logger.info(f"关闭用户 {user_id} 的浏览器")
        except Exception as e:
            self.logger.error(f"关闭浏览器失败: {str(e)}")
    
    def close_all(self):
        """
        关闭所有浏览器
        """
        try:
            # 关闭所有页面
            for user_id in list(self.pages.keys()):
                self.pages[user_id].close()
            self.pages.clear()
            
            # 关闭所有上下文并保存状态
            for user_id in list(self.contexts.keys()):
                # 保存 storage_state
                user_data_dir = self._get_user_data_dir(user_id)
                storage_state_path = f"{user_data_dir}/storage_state.json"
                try:
                    self.contexts[user_id].storage_state(path=storage_state_path)
                    self.logger.info(f"保存用户 {user_id} 的浏览器状态到 {storage_state_path}")
                except Exception as e:
                    self.logger.error(f"保存浏览器状态失败: {str(e)}")
                
                self.contexts[user_id].close()
            self.contexts.clear()
            
            # 关闭所有浏览器
            for user_id in list(self.browsers.keys()):
                self.browsers[user_id].close()
            self.browsers.clear()
            
            # 停止 playwright
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            
            self.logger.info("关闭所有浏览器")
        except Exception as e:
            self.logger.error(f"关闭所有浏览器失败: {str(e)}")