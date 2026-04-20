#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型处理模块
提供截图分析、页面理解、智能决策等能力
"""

import os
import json
import base64
from typing import Optional, Dict, Any
from src.logging_system import Logger


class AIService:
    """大模型服务类"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """初始化大模型服务"""
        self.logger = Logger()
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model or "gpt-4-vision-preview"
        self.logger.info(f"AIService 初始化完成，模型: {self.model}")

    def _load_config(self):
        """从配置文件加载大模型配置"""
        try:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
            ai_config_path = os.path.join(config_dir, "ai_settings.json")
            if os.path.exists(ai_config_path):
                with open(ai_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key", self.api_key)
                    self.base_url = config.get("base_url", self.base_url)
                    self.model = config.get("model", self.model)
                    self.logger.info("大模型配置加载完成")
        except Exception as e:
            self.logger.warning(f"加载大模型配置失败: {e}")

    def analyze_image(self, image_path: str, prompt: str) -> str:
        """
        分析图片并返回结果
        
        Args:
            image_path: 图片路径
            prompt: 分析提示词
            
        Returns:
            大模型返回的分析结果
        """
        if not self.api_key:
            self._load_config()
            if not self.api_key:
                self.logger.warning("大模型 API Key 未配置")
                return ""

        try:
            # 读取图片并转换为 base64
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')

            # 构建请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }

            # 调用大模型 API
            import requests
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                self.logger.info(f"大模型分析完成: {content[:100]}...")
                return content
            else:
                self.logger.error(f"大模型 API 调用失败: {response.status_code}, {response.text}")
                return ""

        except Exception as e:
            self.logger.error(f"大模型分析失败: {e}")
            return ""

    def analyze_page_state(self, screenshot_path: str) -> Dict[str, Any]:
        """
        分析页面状态
        
        Args:
            screenshot_path: 页面截图路径
            
        Returns:
            页面状态分析结果
        """
        prompt = """请分析这个页面截图，返回以下信息（JSON格式）：
{
    "page_type": "页面类型（首页/搜索页/视频页/登录页/其他）",
    "has_popup": "是否有弹窗（true/false）",
    "popup_type": "弹窗类型（如果有）",
    "main_elements": ["主要页面元素列表"],
    "can_interact": "是否可以交互（true/false）",
    "suggestions": ["操作建议"]
}
只返回JSON，不要其他内容。"""

        result = self.analyze_image(screenshot_path, prompt)
        if result:
            try:
                # 提取 JSON
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = result[start:end]
                    return json.loads(json_str)
            except Exception as e:
                self.logger.warning(f"解析大模型返回结果失败: {e}")
        
        return {
            "page_type": "unknown",
            "has_popup": False,
            "popup_type": "",
            "main_elements": [],
            "can_interact": True,
            "suggestions": []
        }

    def find_element_by_description(self, screenshot_path: str, description: str) -> Dict[str, Any]:
        """
        通过描述查找页面元素
        
        Args:
            screenshot_path: 页面截图路径
            description: 元素描述（如"搜索框"、"评论按钮"）
            
        Returns:
            元素位置信息 {"x": int, "y": int, "found": bool}
        """
        prompt = f"""请在这个页面截图中找到"{description}"的位置。
返回JSON格式：
{{"x": 元素中心x坐标, "y": 元素中心y坐标, "found": true/false}}
只返回JSON，不要其他内容。"""

        result = self.analyze_image(screenshot_path, prompt)
        if result:
            try:
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = result[start:end]
                    return json.loads(json_str)
            except Exception as e:
                self.logger.warning(f"解析元素位置失败: {e}")
        
        return {"x": 0, "y": 0, "found": False}

    def extract_text_from_image(self, screenshot_path: str) -> str:
        """
        从图片中提取文字
        
        Args:
            screenshot_path: 图片路径
            
        Returns:
            提取的文字内容
        """
        prompt = "请提取图片中的所有文字内容，保持原有格式。"
        return self.analyze_image(screenshot_path, prompt)

    def decide_next_action(self, screenshot_path: str, goal: str) -> Dict[str, Any]:
        """
        决策下一步操作
        
        Args:
            screenshot_path: 页面截图路径
            goal: 当前目标（如"搜索视频"、"查看评论"）
            
        Returns:
            操作决策 {"action": "操作类型", "target": "目标元素", "reason": "决策原因"}
        """
        prompt = f"""当前目标是：{goal}
请分析页面截图，决策下一步操作。
返回JSON格式：
{{"action": "操作类型（click/type/scroll/wait）", "target": "目标元素描述", "reason": "决策原因"}}
只返回JSON，不要其他内容。"""

        result = self.analyze_image(screenshot_path, prompt)
        if result:
            try:
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = result[start:end]
                    return json.loads(json_str)
            except Exception as e:
                self.logger.warning(f"解析操作决策失败: {e}")
        
        return {"action": "wait", "target": "", "reason": "无法决策"}


# 创建全局单例实例
ai_service = AIService()