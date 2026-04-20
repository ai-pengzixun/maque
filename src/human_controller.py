#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拟人化控制引擎
"""

import math
import random
import time
import pyautogui
from typing import List, Tuple
from src.logging_system import Logger


class HumanController:
    """拟人化控制器类"""

    def __init__(self):
        """初始化拟人化控制器"""
        self.logger = Logger()
        # 启用 PyAutoGUI 的 failsafe 保护
        pyautogui.FAILSAFE = True
        self.logger.info("HumanController 初始化完成")
    
    def calculate_bezier_curve(self, start: Tuple[int, int], end: Tuple[int, int], steps: int = 100) -> List[Tuple[int, int]]:
        """
        计算贝塞尔曲线
        
        Args:
            start: 起点坐标 (x, y)
            end: 终点坐标 (x, y)
            steps: 步数，默认为 100
            
        Returns:
            贝塞尔曲线路径上的点列表
        """
        try:
            # 控制点，生成一个随机的中间点，使路径更自然
            control_point = (
                random.randint(min(start[0], end[0]) - 100, max(start[0], end[0]) + 100),
                random.randint(min(start[1], end[1]) - 100, max(start[1], end[1]) + 100)
            )
            
            path = []
            for t in range(steps + 1):
                t_normalized = t / steps
                # 贝塞尔曲线公式
                x = int((1 - t_normalized) ** 2 * start[0] + 2 * (1 - t_normalized) * t_normalized * control_point[0] + t_normalized ** 2 * end[0])
                y = int((1 - t_normalized) ** 2 * start[1] + 2 * (1 - t_normalized) * t_normalized * control_point[1] + t_normalized ** 2 * end[1])
                path.append((x, y))
            
            return path
        except Exception as e:
            self.logger.error(f"计算贝塞尔曲线失败: {str(e)}")
            return [start, end]
    
    def move_mouse_humanlike(self, start: Tuple[int, int], end: Tuple[int, int], duration: float = 0.5):
        """
        拟人化鼠标移动
        
        Args:
            start: 起点坐标 (x, y)
            end: 终点坐标 (x, y)
            duration: 移动持续时间，默认为 0.5 秒
        """
        try:
            path = self.calculate_bezier_curve(start, end)
            step_duration = duration / len(path)
            
            for point in path:
                pyautogui.moveTo(point[0], point[1], duration=step_duration)
                # 随机微停顿，模拟人类操作
                if random.random() < 0.1:
                    self.smart_sleep(10, 50)
            
            self.logger.info(f"鼠标从 {start} 移动到 {end}")
        except Exception as e:
            self.logger.error(f"鼠标移动失败: {str(e)}")
    
    def generate_random_click_point(self, bounding_box: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """
        在 bounding_box 内生成正态分布的随机点击点
        
        Args:
            bounding_box: (x, y, width, height)
            
        Returns:
            随机点击点坐标 (x, y)
        """
        try:
            x, y, w, h = bounding_box
            # 计算中心区域
            center_x = x + w / 2
            center_y = y + h / 2
            # 中心区域半径
            radius_x = w * 0.3
            radius_y = h * 0.3
            
            # 生成正态分布的随机点
            click_x = int(random.normalvariate(center_x, radius_x / 3))
            click_y = int(random.normalvariate(center_y, radius_y / 3))
            
            # 确保点在 bounding_box 内
            click_x = max(x, min(click_x, x + w))
            click_y = max(y, min(click_y, y + h))
            
            return (click_x, click_y)
        except Exception as e:
            self.logger.error(f"生成随机点击点失败: {str(e)}")
            # 返回中心点作为默认值
            x, y, w, h = bounding_box
            return (x + w // 2, y + h // 2)
    
    def click_humanlike(self, bounding_box: Tuple[int, int, int, int]):
        """
        拟人化点击
        
        Args:
            bounding_box: (x, y, width, height)
        """
        try:
            # 获取当前鼠标位置
            current_pos = pyautogui.position()
            # 生成随机点击点
            click_point = self.generate_random_click_point(bounding_box)
            # 移动到点击点
            self.move_mouse_humanlike(current_pos, click_point)
            # 随机延迟
            self.smart_sleep(100, 300)
            # 点击
            pyautogui.click(click_point[0], click_point[1])
            # 随机延迟
            self.smart_sleep(100, 300)
            
            self.logger.info(f"在 {click_point} 位置执行点击")
        except Exception as e:
            self.logger.error(f"点击操作失败: {str(e)}")
    
    def smart_sleep(self, min_ms: int, max_ms: int):
        """
        智能延迟，模拟人类操作的不确定性
        
        Args:
            min_ms: 最小延迟时间（毫秒）
            max_ms: 最大延迟时间（毫秒）
        """
        try:
            # 转换为秒
            min_sec = min_ms / 1000
            max_sec = max_ms / 1000
            # 生成随机延迟
            delay = random.uniform(min_sec, max_sec)
            time.sleep(delay)
        except Exception as e:
            self.logger.error(f"延迟操作失败: {str(e)}")
    
    def type_humanlike(self, text: str, typing_speed: float = 0.1):
        """
        拟人化输入
        
        Args:
            text: 要输入的文本
            typing_speed: 平均打字速度（秒/字符）
        """
        try:
            for char in text:
                pyautogui.typewrite(char)
                # 随机延迟，模拟人类打字速度
                self.smart_sleep(int(typing_speed * 500), int(typing_speed * 1500))
            
            self.logger.info(f"输入文本: {text}")
        except Exception as e:
            self.logger.error(f"输入操作失败: {str(e)}")
    
    def screenshot(self, region: Tuple[int, int, int, int] = None) -> str:
        """
        截图
        
        Args:
            region: 截图区域 (x, y, width, height)，None 表示全屏
            
        Returns:
            截图保存路径
        """
        try:
            import os
            # 确保 data/errors 目录存在
            if not os.path.exists("data/errors"):
                os.makedirs("data/errors")
            
            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"data/errors/screenshot_{timestamp}.png"
            
            # 截图
            if region:
                pyautogui.screenshot(screenshot_path, region=region)
            else:
                pyautogui.screenshot(screenshot_path)
            
            self.logger.info(f"截图保存到: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            self.logger.error(f"截图操作失败: {str(e)}")
            return ""