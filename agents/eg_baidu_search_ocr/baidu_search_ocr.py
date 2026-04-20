#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度搜索OCR Robot Framework Library
使用OCR技术进行百度搜索操作，通过视觉识别而非DOM元素定位
"""

import logging
import io
# 配置日志
logger = logging.getLogger(__name__)

# 可选导入OCR相关库
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None
    np = None

try:
    import pytesseract
    HAS_PYTESSERACT = True
    # 直接指定Tesseract路径，不依赖环境变量
    # import os
    # tesseract_path = r"D:\ProgramFiles\Tesseract-OCR\tesseract.exe"
    # if os.path.exists(tesseract_path):
    #     pytesseract.pytesseract.tesseract_cmd = tesseract_path
    #     logger.info(f"已设置Tesseract路径: {tesseract_path}")
    # else:
    #     logger.warning(f"Tesseract路径不存在: {tesseract_path}")
except ImportError:
    HAS_PYTESSERACT = False
    pytesseract = None

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None

from src.jjrj_config import JjrjConfig
from src.browser_manager import BrowserManager
from src.human_controller import HumanController


class BaiduSearchOCRLibrary:
    """百度搜索OCR Robot Framework 关键词库 - 使用OCR技术完成搜索操作"""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self):
        logger.info("初始化 BaiduSearchOCRLibrary...")
        logger.info(f"OCR依赖状态 - cv2: {HAS_CV2}, pytesseract: {HAS_PYTESSERACT}, PIL: {HAS_PIL}")
        
        if not HAS_PYTESSERACT:
            logger.warning("pytesseract 未安装，OCR功能将不可用。请运行: pip install pytesseract")
        
        if not HAS_CV2:
            logger.warning("opencv-python 未安装，图像处理功能将不可用。请运行: pip install opencv-python")
        
        if not HAS_PIL:
            logger.warning("Pillow 未安装，图像处理功能将不可用。请运行: pip install Pillow")
        
        self.browser_manager = BrowserManager()
        self.human = HumanController()
        self.page = None
        self.user_id = "baidu_search_ocr"
        
        # 检测Tesseract OCR引擎是否可用
        self.tesseract_available = self._check_tesseract_available()
        
        logger.info("BaiduSearchOCRLibrary 初始化完成")

    def _check_tesseract_available(self) -> bool:
        """
        检测Tesseract OCR引擎是否可用
        
        Returns:
            bool: Tesseract是否可用
        """
        if not HAS_PYTESSERACT:
            logger.warning("pytesseract包未安装")
            return False
        
        try:
            # 尝试获取Tesseract版本来检测是否安装
            version = pytesseract.get_tesseract_version()
            logger.info(f"✓ Tesseract OCR引擎可用，版本: {version}")
            return True
        except Exception as e:
            logger.warning(f"✗ Tesseract OCR引擎不可用: {e}")
            logger.warning("将使用默认坐标模式进行百度搜索")
            logger.warning("如需使用OCR功能，请安装Tesseract: https://github.com/tesseract-ocr/tesseract")
            return False

    def _screenshot_to_numpy(self):
        """将页面截图转换为numpy数组"""
        logger.info("开始页面截图...")
        if not self.page:
            raise RuntimeError("页面未打开，无法截图")
        
        screenshot_bytes = self.page.screenshot()
        logger.info(f"截图完成，大小: {len(screenshot_bytes)} 字节")
        
        if not HAS_PIL:
            raise RuntimeError("Pillow 未安装，无法处理图像")
        
        image = Image.open(io.BytesIO(screenshot_bytes))
        logger.info(f"图像加载成功，尺寸: {image.size}")
        
        if HAS_CV2:
            return np.array(image), image
        else:
            # 如果没有cv2，只返回PIL图像
            return None, image

    def _find_element_by_ocr(self, target_text, screenshot=None, image_pil=None, confidence_threshold=60):
        """
        使用OCR查找包含目标文本的元素位置
        
        Args:
            target_text: 要查找的文本
            screenshot: 截图的numpy数组（可选）
            image_pil: PIL图像对象（可选）
            confidence_threshold: OCR置信度阈值
            
        Returns:
            tuple: (center_x, center_y, width, height) 或 None
        """
        logger.info(f"开始OCR查找: '{target_text}'")
        
        if not self.tesseract_available:
            logger.warning("Tesseract不可用，跳过OCR查找")
            return None
        
        if not HAS_PIL:
            logger.error("Pillow 未安装，无法处理图像")
            return None
        
        if image_pil is None:
            screenshot, image_pil = self._screenshot_to_numpy()
        
        logger.info(f"使用OCR识别图像中的文本，置信度阈值: {confidence_threshold}%")
        
        try:
            # 使用OCR识别文本
            ocr_data = pytesseract.image_to_data(image_pil, output_type=pytesseract.Output.DICT, lang='chi_sim+eng')
            
            n_boxes = len(ocr_data['text'])
            logger.info(f"OCR识别到 {n_boxes} 个文本块")
            
            for i in range(n_boxes):
                text = ocr_data['text'][i].strip()
                conf = int(ocr_data['conf'][i])
                
                # 检查是否包含目标文本
                if conf > confidence_threshold and target_text.lower() in text.lower():
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    logger.info(f"✓ OCR找到 '{target_text}': 位置=({center_x}, {center_y}), 大小=({w}x{h}), 置信度={conf}%")
                    return (center_x, center_y, w, h)
            
            logger.warning(f"✗ OCR未找到包含 '{target_text}' 的元素")
            return None
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return None

    def _click_by_coordinates(self, x, y):
        """
        通过坐标点击页面
        
        Args:
            x: X坐标
            y: Y坐标
        """
        logger.info(f"准备点击坐标: ({x}, {y})")
        if not self.page:
            raise RuntimeError("页面未打开，无法点击")
        
        self.page.mouse.click(x, y)
        logger.info(f"✓ 点击完成: ({x}, {y})")

    def _type_by_coordinates(self, x, y, text):
        """
        在指定坐标输入文本
        
        Args:
            x: X坐标
            y: Y坐标
            text: 要输入的文本
        """
        logger.info(f"准备在坐标 ({x}, {y}) 输入: {text}")
        if not self.page:
            raise RuntimeError("页面未打开，无法输入")
        
        self.page.mouse.click(x, y)
        logger.info(f"已点击坐标 ({x}, {y})，等待焦点...")
        self.human.smart_sleep(300, 500)
        
        # 清空现有内容
        active_tag = self.page.evaluate("() => document.activeElement.tagName")
        logger.info(f"当前焦点元素: {active_tag}")
        
        if active_tag in ['INPUT', 'TEXTAREA']:
            logger.info("清空现有内容...")
            self.page.keyboard.press("Control+a")
            self.human.smart_sleep(100, 200)
            self.page.keyboard.press("Delete")
            self.human.smart_sleep(100, 200)
        
        # 输入文本
        logger.info(f"开始输入文本: {text}")
        self.page.keyboard.type(text, delay=50)
        logger.info(f"✓ 输入完成: {text}")

    def open_baidu_with_ocr(self):
        """使用OCR打开百度首页"""
        logger.info("=" * 60)
        logger.info("开始执行: Open Baidu With OCR")
        logger.info("=" * 60)
        
        env_config = JjrjConfig.get_env_config()
        chrome_path = env_config.get("chrome_path", "") or None
        user_data_path = env_config.get("user_data_path", "") or None
        
        logger.info(f"Chrome路径: {chrome_path or '默认'}")
        logger.info(f"用户数据路径: {user_data_path or '默认'}")

        logger.info("启动浏览器...")
        browser = self.browser_manager.launch_browser(
            self.user_id,
            headless=False,
            browser_exec_path=chrome_path
        )
        logger.info("浏览器启动成功")

        context_options = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        if user_data_path:
            import os
            storage_state_path = os.path.join(user_data_path, "storage_state.json")
            if os.path.exists(storage_state_path):
                context_options["storage_state"] = storage_state_path
                logger.info(f"使用存储状态: {storage_state_path}")

        logger.info("创建浏览器上下文...")
        context = browser.new_context(**context_options)
        self.page = context.new_page()
        self.browser_manager._load_stealth(self.page)
        logger.info("页面创建完成，已加载反检测脚本")
        
        logger.info("导航到百度首页...")
        try:
            self.page.goto("https://www.baidu.com", wait_until="domcontentloaded", timeout=15000)
            logger.info("✓ 页面 domcontentloaded 完成")
        except Exception as e:
            logger.warning(f"domcontentloaded 等待超时: {e}")
            logger.info("回退到 load 状态等待...")
            self.page.goto("https://www.baidu.com", wait_until="load", timeout=15000)
            logger.info("✓ 页面 load 完成")
        
        self.human.smart_sleep(1000, 2000)
        
        # 使用OCR验证页面是否成功加载
        logger.info("开始OCR验证页面加载...")
        try:
            screenshot, image_pil = self._screenshot_to_numpy()
            baidu_logo = self._find_element_by_ocr("百度", screenshot, image_pil)
            
            if baidu_logo:
                logger.info("✓ OCR确认百度首页加载成功")
            else:
                logger.warning("✗ OCR未识别到百度logo，但继续执行")
        except Exception as e:
            logger.warning(f"OCR验证失败: {e}")
        
        logger.info("✓ Open Baidu With OCR 执行完成")

    def search_keyword_with_ocr(self, keyword):
        """
        使用OCR在百度搜索关键词
        
        Args:
            keyword: 搜索关键词
        """
        logger.info("=" * 60)
        logger.info(f"开始执行: Search Keyword With OCR, 关键词: {keyword}")
        logger.info("=" * 60)
        
        if not self.page:
            raise RuntimeError("页面未打开，请先调用 Open Baidu With OCR")
        
        logger.info(f"开始使用OCR搜索关键词: {keyword}")
        
        search_box = None
        
        # 如果Tesseract可用，尝试使用OCR查找搜索框
        if self.tesseract_available:
            logger.info("Tesseract可用，尝试使用OCR查找搜索框...")
            try:
                # 截图进行OCR识别
                logger.info("截取当前页面...")
                screenshot, image_pil = self._screenshot_to_numpy()
                
                # 使用OCR查找搜索框（通常包含"搜索"或placeholder文本）
                logger.info("OCR查找搜索框...")
                search_box = self._find_element_by_ocr("搜索", screenshot, image_pil)
                
                if not search_box:
                    logger.info("未找到'搜索'，尝试查找'百度一下'...")
                    # 尝试查找其他可能的搜索框标识
                    search_box = self._find_element_by_ocr("百度一下", screenshot, image_pil)
            except Exception as e:
                logger.warning(f"OCR查找失败: {e}")
                search_box = None
        
        if not search_box:
            # 如果OCR不可用或找不到，使用页面中心偏上位置作为备选
            logger.warning("✗ 使用默认搜索框位置（OCR不可用或未找到）")
            page_width = self.page.evaluate("() => window.innerWidth")
            page_height = self.page.evaluate("() => window.innerHeight")
            search_box = (page_width // 2, page_height // 3, 200, 40)
            logger.info(f"使用默认搜索框位置: ({search_box[0]}, {search_box[1]})")
        
        center_x, center_y, box_w, box_h = search_box
        
        # 点击搜索框并输入关键词
        logger.info(f"点击搜索框位置: ({center_x}, {center_y})")
        self._type_by_coordinates(center_x, center_y, keyword)
        
        self.human.smart_sleep(500, 1000)
        
        # 尝试查找搜索按钮
        search_button = None
        if self.tesseract_available:
            try:
                # 重新截图查找搜索按钮
                logger.info("重新截图查找搜索按钮...")
                screenshot, image_pil = self._screenshot_to_numpy()
                
                # 使用OCR查找"百度一下"按钮
                logger.info("OCR查找'百度一下'按钮...")
                search_button = self._find_element_by_ocr("百度一下", screenshot, image_pil)
            except Exception as e:
                logger.warning(f"OCR查找搜索按钮失败: {e}")
                search_button = None
        
        if search_button:
            btn_x, btn_y, btn_w, btn_h = search_button
            logger.info(f"点击搜索按钮位置: ({btn_x}, {btn_y})")
            self._click_by_coordinates(btn_x, btn_y)
        else:
            # 如果找不到搜索按钮，按回车键
            logger.warning("✗ 使用回车键提交搜索（OCR不可用或未找到按钮）")
            self.page.keyboard.press("Enter")
            logger.info("✓ 已按回车键提交搜索")
        
        self.human.smart_sleep(2000, 3000)
        logger.info("✓ OCR搜索完成")

    def get_page_title(self):
        """获取当前页面标题"""
        logger.info("获取页面标题...")
        if not self.page:
            raise RuntimeError("页面未打开")
        title = self.page.title()
        logger.info(f"页面标题: {title}")
        return title

    def close_all_browsers(self):
        """关闭所有浏览器"""
        logger.info("关闭所有浏览器...")
        self.browser_manager.close_all()
        self.page = None
        logger.info("✓ 浏览器已关闭")
