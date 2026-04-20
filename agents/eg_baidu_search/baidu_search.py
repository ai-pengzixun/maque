#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度搜索 Robot Framework Library
提供基于 Playwright 的百度搜索关键词
"""

import logging
from src.jjrj_config import JjrjConfig
from src.browser_manager import BrowserManager
from src.human_controller import HumanController

# 配置日志
logger = logging.getLogger(__name__)


class BaiduSearchLibrary:
    """百度搜索 Robot Framework 关键词库"""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self):
        self.browser_manager = BrowserManager()
        self.human = HumanController()
        self.page = None
        self.user_id = "baidu_search"

    def open_baidu(self):
        """打开百度首页"""
        env_config = JjrjConfig.get_env_config()
        chrome_path = env_config.get("chrome_path", "") or None
        user_data_path = env_config.get("user_data_path", "") or None

        browser = self.browser_manager.launch_browser(
            self.user_id,
            headless=False,
            browser_exec_path=chrome_path
        )

        context_options = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        if user_data_path:
            import os
            storage_state_path = os.path.join(user_data_path, "storage_state.json")
            if os.path.exists(storage_state_path):
                context_options["storage_state"] = storage_state_path

        context = browser.new_context(**context_options)
        self.page = context.new_page()
        self.browser_manager._load_stealth(self.page)
        # 使用更快的等待策略，避免 networkidle 超时
        logger.info("导航到百度首页，等待页面加载...")
        try:
            # 先尝试等待 domcontentloaded，这是最快的
            self.page.goto("https://www.baidu.com", wait_until="domcontentloaded", timeout=15000)
            logger.info("页面 domcontentloaded 完成")
        except Exception as e:
            logger.warning(f"domcontentloaded 等待超时: {e}")
            # 回退到 load 状态
            logger.info("回退到 load 状态等待...")
            self.page.goto("https://www.baidu.com", wait_until="load", timeout=15000)
            logger.info("页面 load 完成")
        
        # 等待搜索框出现
        logger.info("等待搜索框元素出现...")
        try:
            self.page.wait_for_selector("#kw", timeout=10000)
            logger.info("搜索框元素已出现")
        except Exception as e:
            logger.warning(f"搜索框元素等待超时: {e}")
        
        self.human.smart_sleep(1000, 2000)

    def search_keyword(self, keyword):
        """在百度搜索关键词 - 多方法定位"""
        if not self.page:
            raise RuntimeError("页面未打开，请先调用 Open Baidu")
        
        logger.info(f"开始搜索关键词: {keyword}")
        
        # 1. 尝试 DOM 定位（ID 定位）
        logger.info("尝试 DOM 定位 - ID 选择器 '#kw'")
        try:
            logger.info("等待搜索框可见...")
            self.page.wait_for_selector("#kw", state="visible", timeout=10000)
            logger.info("DOM 定位成功！")
            search_selector = "#kw"
        except Exception as e:
            logger.warning(f"DOM 定位失败: {e}")
            
            # 2. 尝试 CSS 定位（placeholder 定位）
            logger.info("尝试 CSS 定位 - placeholder 选择器 'input[placeholder*=搜索]'")
            try:
                logger.info("等待搜索框可见...")
                self.page.wait_for_selector("input[placeholder*=搜索]", state="visible", timeout=10000)
                logger.info("CSS 定位成功！")
                search_selector = "input[placeholder*=搜索]"
            except Exception as e:
                logger.warning(f"CSS 定位失败: {e}")
                
                # 3. 尝试 CSS 定位（name 属性定位）
                logger.info("尝试 CSS 定位 - name 选择器 'input[name=wd]'")
                try:
                    logger.info("等待搜索框可见...")
                    self.page.wait_for_selector("input[name=wd]", state="visible", timeout=10000)
                    logger.info("CSS name 定位成功！")
                    search_selector = "input[name=wd]"
                except Exception as e:
                    logger.warning(f"CSS name 定位失败: {e}")
                    
                    # 4. 尝试 CSS 定位（class 定位）
                    logger.info("尝试 CSS 定位 - class 选择器 '.s_ipt'")
                    try:
                        logger.info("等待搜索框可见...")
                        self.page.wait_for_selector(".s_ipt", state="visible", timeout=10000)
                        logger.info("CSS class 定位成功！")
                        search_selector = ".s_ipt"
                    except Exception as e:
                        logger.warning(f"CSS class 定位失败: {e}")
                        
                        # 5. 尝试 XPath 定位
                        logger.info("尝试 XPath 定位 - '//input[@id='kw']'")
                        try:
                            logger.info("等待搜索框可见...")
                            self.page.wait_for_selector("//input[@id='kw']", state="visible", timeout=10000)
                            logger.info("XPath 定位成功！")
                            search_selector = "//input[@id='kw']"
                        except Exception as e:
                            logger.warning(f"XPath 定位失败: {e}")
                            
                            # 6. 尝试 JavaScript 定位（作为最后手段）
                            logger.info("尝试 JavaScript 定位")
                            try:
                                logger.info("执行 JavaScript 查找搜索框...")
                                search_box = self.page.evaluate("() => document.getElementById('kw') || document.querySelector('input[name=wd]') || document.querySelector('.s_ipt')")
                                if search_box:
                                    logger.info("JavaScript 定位成功！")
                                    search_selector = "#kw"  # 默认回退到 ID 选择器
                                else:
                                    raise Exception("所有定位方法都失败")
                            except Exception as e:
                                logger.error(f"所有定位方法都失败: {e}")
                                raise RuntimeError("无法定位搜索框，请检查页面结构")
        
        # 输入关键词
        try:
            logger.info(f"在搜索框中输入: {keyword}")
            self.page.fill(search_selector, keyword)
            logger.info("关键词输入成功")
            self.human.smart_sleep(500, 1000)
        except Exception as e:
            logger.error(f"输入关键词失败: {e}")
            # 尝试直接通过 JavaScript 输入
            logger.info("尝试通过 JavaScript 输入关键词")
            try:
                self.page.evaluate(f"(selector, text) => document.querySelector(selector).value = text", search_selector, keyword)
                logger.info("JavaScript 输入成功")
                self.human.smart_sleep(500, 1000)
            except Exception as e:
                logger.error(f"JavaScript 输入也失败: {e}")
                raise RuntimeError("无法输入关键词")
        
        # 执行搜索
        try:
            # 尝试点击搜索按钮
            logger.info("尝试定位并点击搜索按钮")
            try:
                logger.info("等待搜索按钮可见...")
                self.page.wait_for_selector("#su", state="visible", timeout=5000)
                logger.info("搜索按钮定位成功，执行点击")
                self.page.click("#su")
                logger.info("搜索按钮点击成功")
            except Exception as e:
                logger.warning(f"点击搜索按钮失败: {e}")
                # 尝试按回车键
                logger.info("尝试按回车键执行搜索")
                self.page.press(search_selector, "Enter")
                logger.info("回车键执行搜索成功")
            
            self.human.smart_sleep(2000, 3000)
            logger.info("搜索完成")
        except Exception as e:
            logger.error(f"执行搜索失败: {e}")
            # 最后尝试 JavaScript 提交
            logger.info("尝试通过 JavaScript 提交搜索")
            try:
                self.page.evaluate("() => document.getElementById('su').click() || document.querySelector('form').submit()")
                logger.info("JavaScript 提交搜索成功")
                self.human.smart_sleep(2000, 3000)
            except Exception as e:
                logger.error(f"JavaScript 提交也失败: {e}")
                raise RuntimeError("无法执行搜索")

    def get_page_title(self):
        """获取当前页面标题"""
        if not self.page:
            raise RuntimeError("页面未打开")
        return self.page.title()

    def close_all_browsers(self):
        """关闭所有浏览器"""
        self.browser_manager.close_all()
        self.page = None
