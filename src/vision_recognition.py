#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视觉识别模块
"""

import os
import cv2
import numpy as np
import pyautogui
from typing import Optional, Tuple, List
from PySide6.QtCore import QThread, Signal
from src.logging_system import Logger
from src.human_controller import HumanController


class VisionRecognition:
    """视觉识别类"""

    def __init__(self):
        """初始化视觉识别"""
        self.logger = Logger()
        self.human = HumanController()
        # 延迟导入 PaddleOCR，避免启动时的性能开销
        self.ocr = None
        # 不立即初始化 OCR，只在实际使用时初始化
        self.logger.info("VisionRecognition 初始化完成")
    
    def _init_ocr(self):
        """初始化 OCR"""
        # 如果已经尝试过初始化但失败，不再重复尝试
        if hasattr(self, '_ocr_init_failed') and self._ocr_init_failed:
            return None
            
        try:
            from paddleocr import PaddleOCR
            import os
            # 禁用 oneDNN 以避免兼容性问题
            os.environ["FLAGS_use_mkldnn"] = "0"
            # 使用 PaddleOCR，设置为中文识别，禁用GPU和oneDNN
            self.ocr = PaddleOCR(
                use_angle_cls=True, 
                lang="ch",
                use_gpu=False,
                enable_mkldnn=False  # 禁用 oneDNN
            )
            self.logger.info("PaddleOCR 初始化完成（已禁用oneDNN）")
        except Exception as e:
            self.logger.error(f"初始化 PaddleOCR 失败: {str(e)}")
            self._ocr_init_failed = True  # 标记初始化失败
            self.ocr = None
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """
        截取当前屏幕
        
        Returns:
            屏幕截图的 numpy 数组
        """
        try:
            # 使用 PyAutoGUI 截图
            screenshot = pyautogui.screenshot()
            # 转换为 numpy 数组
            screen_array = np.array(screenshot)
            # 转换颜色空间（BGR to RGB）
            screen_array = cv2.cvtColor(screen_array, cv2.COLOR_RGB2BGR)
            self.logger.info("屏幕截图完成")
            return screen_array
        except Exception as e:
            self.logger.error(f"截图失败: {str(e)}")
            return None
    
    def find_text(self, text: str, screenshot: Optional[np.ndarray] = None) -> Optional[Tuple[int, int]]:
        """
        识别屏幕上的文字并返回中心坐标
        
        Args:
            text: 要识别的文字
            screenshot: 屏幕截图，如果为 None 则自动截取
            
        Returns:
            文字中心坐标 (x, y)，如果未找到返回 None
        """
        try:
            # 如果没有截图，自动截取
            if screenshot is None:
                screenshot = self.capture_screen()
                if screenshot is None:
                    return None
            
            # 确保 OCR 已初始化
            if self.ocr is None:
                # 如果已经标记为初始化失败，直接返回
                if hasattr(self, '_ocr_init_failed') and self._ocr_init_failed:
                    return None
                self._init_ocr()
                if self.ocr is None:
                    return None
            
            # 使用 OCR 识别文字（使用 predict 方法）
            try:
                result = self.ocr.predict(screenshot)
            except Exception as e:
                self.logger.debug(f"OCR predict 失败: {e}")
                self.logger.warning("OCR 功能暂时不可用，将跳过 OCR 辅助定位")
                self.ocr = None  # 标记 OCR 不可用，避免重复尝试
                return None
            
            # 遍历识别结果
            for line in result:
                for word_info in line:
                    recognized_text = word_info[1][0]
                    confidence = word_info[1][1]
                    
                    # 检查是否匹配目标文字
                    if text in recognized_text and confidence > 0.8:
                        # 获取文字的 bounding box
                        bbox = word_info[0]
                        # 计算中心坐标
                        x = int((bbox[0][0] + bbox[2][0]) / 2)
                        y = int((bbox[0][1] + bbox[2][1]) / 2)
                        self.logger.debug(f"找到文字 '{text}'，坐标: ({x}, {y})，置信度: {confidence}")
                        return (x, y)
            
            self.logger.debug(f"未找到文字 '{text}'")
            return None
        except Exception as e:
            self.logger.debug(f"文字识别失败: {str(e)}")
            return None
    
    def find_text_and_click(self, text: str):
        """
        识别屏幕上的文字并点击
        
        Args:
            text: 要识别的文字
        """
        try:
            # 查找文字坐标
            coord = self.find_text(text)
            if coord is not None:
                # 获取当前鼠标位置
                current_pos = pyautogui.position()
                # 计算 bounding box（假设文字高度为 30px）
                bounding_box = (coord[0] - 50, coord[1] - 15, 100, 30)
                # 使用 HumanController 进行拟人化点击
                self.human.click_humanlike(bounding_box)
            else:
                self.logger.warning(f"未找到文字 '{text}'，无法点击")
        except Exception as e:
            self.logger.error(f"文字点击失败: {str(e)}")
    
    def find_image(self, template_path: str, threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        使用模板匹配寻找屏幕上的特定图标
        
        Args:
            template_path: 模板图片路径
            threshold: 相似度阈值，默认为 0.8
            
        Returns:
            图标中心坐标 (x, y)，如果未找到返回 None
        """
        try:
            # 检查模板文件是否存在
            if not os.path.exists(template_path):
                self.logger.error(f"模板文件不存在: {template_path}")
                return None
            
            # 截取屏幕
            screenshot = self.capture_screen()
            if screenshot is None:
                return None
            
            # 读取模板图片
            template = cv2.imread(template_path)
            if template is None:
                self.logger.error(f"读取模板图片失败: {template_path}")
                return None
            
            # 获取模板尺寸
            template_height, template_width = template.shape[:2]
            
            # 使用模板匹配
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            
            # 找到匹配度最高的位置
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 检查是否达到阈值
            if max_val >= threshold:
                # 计算中心坐标
                center_x = max_loc[0] + template_width // 2
                center_y = max_loc[1] + template_height // 2
                self.logger.info(f"找到图像，坐标: ({center_x}, {center_y})，相似度: {max_val}")
                return (center_x, center_y)
            else:
                self.logger.warning(f"未找到图像，最高相似度: {max_val}")
                return None
        except Exception as e:
            self.logger.error(f"图像匹配失败: {str(e)}")
            return None
    
    def find_image_and_click(self, template_path: str, threshold: float = 0.8):
        """
        寻找屏幕上的特定图标并点击
        
        Args:
            template_path: 模板图片路径
            threshold: 相似度阈值，默认为 0.8
        """
        try:
            # 查找图像坐标
            coord = self.find_image(template_path, threshold)
            if coord is not None:
                # 获取当前鼠标位置
                current_pos = pyautogui.position()
                # 计算 bounding box
                template = cv2.imread(template_path)
                if template is not None:
                    template_height, template_width = template.shape[:2]
                    bounding_box = (coord[0] - template_width // 2, coord[1] - template_height // 2, template_width, template_height)
                    # 使用 HumanController 进行拟人化点击
                    self.human.click_humanlike(bounding_box)
            else:
                self.logger.warning(f"未找到图像 '{template_path}'，无法点击")
        except Exception as e:
            self.logger.error(f"图像点击失败: {str(e)}")


class VisionRecognitionThread(QThread):
    """视觉识别线程"""
    
    # 信号定义
    text_found = Signal(tuple)  # (x, y)
    text_not_found = Signal()
    image_found = Signal(tuple)  # (x, y)
    image_not_found = Signal()
    error = Signal(str)
    
    def __init__(self, vision: VisionRecognition):
        """
        初始化视觉识别线程
        
        Args:
            vision: VisionRecognition 实例
        """
        super().__init__()
        self.vision = vision
        self.task_type = None
        self.text = None
        self.template_path = None
        self.threshold = 0.8
    
    def set_find_text_task(self, text: str):
        """
        设置查找文字任务
        
        Args:
            text: 要查找的文字
        """
        self.task_type = "find_text"
        self.text = text
    
    def set_find_image_task(self, template_path: str, threshold: float = 0.8):
        """
        设置查找图像任务
        
        Args:
            template_path: 模板图片路径
            threshold: 相似度阈值
        """
        self.task_type = "find_image"
        self.template_path = template_path
        self.threshold = threshold
    
    def run(self):
        """
        运行视觉识别任务
        """
        try:
            if self.task_type == "find_text" and self.text:
                # 查找文字
                coord = self.vision.find_text(self.text)
                if coord:
                    self.text_found.emit(coord)
                else:
                    self.text_not_found.emit()
            elif self.task_type == "find_image" and self.template_path:
                # 查找图像
                coord = self.vision.find_image(self.template_path, self.threshold)
                if coord:
                    self.image_found.emit(coord)
                else:
                    self.image_not_found.emit()
        except Exception as e:
            self.error.emit(str(e))