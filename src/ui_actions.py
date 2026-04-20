#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI自动化原子动作库 - 框架级支持代码
实现统一执行策略：DOM → OCR → LLM fallback → verify → retry
适用于所有Agent调用
"""

import logging
from typing import Any, Optional, List, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ActionParams:
    """UI动作参数类"""
    target: str                           # selector / 文本 / OCR描述
    value: Any = None                    # 输入值 / 文件路径 / 按键等
    timeout: float = 5.0                 # 超时时间（秒）
    retry: int = 3                       # 重试次数
    strategy: list = field(default_factory=lambda: ["dom", "ocr", "llm"])  # 策略列表
    extra: dict = field(default_factory=dict)  # 扩展参数


@dataclass
class ActionResult:
    """UI动作返回结果类"""
    success: bool
    data: Any = None
    error: str = ""
    method: str = ""                     # dom / ocr / llm


def verify_not_none(result):
    """验证结果不为None"""
    return result is not None


def verify_true(result):
    """验证结果为True"""
    return result is True


def verify_text(element, expected):
    """验证元素文本匹配"""
    try:
        return element.text == expected
    except Exception:
        return False


def execute_with_fallback(
    params: ActionParams,
    try_dom: Callable,
    try_ocr: Callable,
    try_llm: Callable,
    verify: Callable
) -> ActionResult:
    """
    统一执行策略：DOM → OCR → LLM fallback
    """
    for attempt in range(params.retry):
        if params.retry > 1:
            logger.debug(f"执行尝试 {attempt + 1}/{params.retry}")
        
        # DOM策略
        if "dom" in params.strategy:
            try:
                logger.debug("尝试DOM策略...")
                result = try_dom(params)
                if verify(result):
                    logger.info("✓ DOM策略成功")
                    return ActionResult(True, result, method="dom")
            except Exception as e:
                logger.debug(f"DOM策略失败: {e}")
        
        # OCR策略
        if "ocr" in params.strategy:
            try:
                logger.debug("尝试OCR策略...")
                result = try_ocr(params)
                if verify(result):
                    logger.info("✓ OCR策略成功")
                    return ActionResult(True, result, method="ocr")
            except Exception as e:
                logger.debug(f"OCR策略失败: {e}")
        
        # LLM策略
        if "llm" in params.strategy:
            try:
                logger.debug("尝试LLM策略...")
                result = try_llm(params)
                if verify(result):
                    logger.info("✓ LLM策略成功")
                    return ActionResult(True, result, method="llm")
            except Exception as e:
                logger.debug(f"LLM策略失败: {e}")
    
    # 不输出warning，由调用方决定如何处理失败
    return ActionResult(False, error="All strategies failed")


class UIActions:
    """UI自动化原子动作库"""
    
    def __init__(self, page, human_controller=None, vision=None, ai_service=None):
        """
        初始化UI动作库
        
        Args:
            page: Playwright页面对象
            human_controller: 人工控制器
            vision: 视觉识别模块
            ai_service: AI服务模块
        """
        self.page = page
        self.human = human_controller
        self.vision = vision
        self.ai_service = ai_service
        
        # 标记OCR和AI是否可用（一旦失败就不再尝试）
        self._ocr_disabled = False
        self._ai_disabled = False
    
    def _is_ocr_available(self):
        """检查OCR是否可用"""
        if self._ocr_disabled:
            return False
        if not self.vision:
            self._ocr_disabled = True
            return False
        return True
    
    def _is_ai_available(self):
        """检查AI服务是否可用"""
        if self._ai_disabled:
            return False
        if not self.ai_service:
            self._ai_disabled = True
            return False
        return True
    
    def _smart_sleep(self, min_ms=300, max_ms=600):
        """智能延迟"""
        if self.human:
            self.human.smart_sleep(min_ms, max_ms)
        else:
            import time
            time.sleep((min_ms + max_ms) / 2000)
    
    def _get_screenshot_for_ocr(self):
        """获取截图用于OCR识别"""
        import io
        from PIL import Image
        import numpy as np
        import cv2
        
        screenshot = self.page.screenshot()
        image = Image.open(io.BytesIO(screenshot))
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # ==================== 感知类（Perception）====================
    
    def find_element(self, params: ActionParams) -> ActionResult:
        """定位单个元素"""
        def try_dom(p):
            self.page.wait_for_selector(p.target, state="visible", timeout=p.timeout * 1000)
            return self.page.query_selector(p.target)
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            screenshot = self.page.screenshot()
            import io
            from PIL import Image
            import numpy as np
            import cv2
            image = Image.open(io.BytesIO(screenshot))
            screenshot_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            coord = self.vision.find_text(p.target, screenshot_np)
            if coord:
                return {"type": "ocr_coord", "x": coord[0], "y": coord[1]}
            return None
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"找到元素: {p.target}")
            return result
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_not_none)
    
    def find_elements(self, params: ActionParams) -> ActionResult:
        """获取元素列表"""
        def try_dom(p):
            elements = self.page.query_selector_all(p.target)
            return elements if elements else None
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            coords = self.vision.find_all_text(p.target)
            return coords if coords else None
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"找到所有元素: {p.target}")
            return result
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, lambda r: r is not None and len(r) > 0)
    
    def element_exists(self, params: ActionParams) -> ActionResult:
        """判断元素是否存在"""
        def try_dom(p):
            try:
                el = self.page.query_selector(p.target)
                return el is not None and el.is_visible()
            except Exception:
                return False
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            screenshot_np = self._get_screenshot_for_ocr()
            coord = self.vision.find_text(p.target, screenshot_np)
            return coord is not None
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"判断元素是否存在: {p.target}")
            return "存在" in result or "yes" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    def get_text(self, params: ActionParams) -> ActionResult:
        """获取文本（OCR fallback）"""
        def try_dom(p):
            el = self.page.query_selector(p.target)
            if el:
                return el.inner_text()
            return None
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            coord = self.vision.find_text(p.target)
            if coord:
                return {"text": p.target, "coord": coord}
            return None
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"提取文本: {p.target}")
            return result
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_not_none)
    
    def get_attribute(self, params: ActionParams) -> ActionResult:
        """获取属性"""
        def try_dom(p):
            el = self.page.query_selector(p.target)
            if el:
                attr_name = p.extra.get("attribute", "href")
                return el.get_attribute(attr_name)
            return None
        
        def try_ocr(p):
            raise Exception("OCR不支持获取属性")
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            attr_name = p.extra.get("attribute", "href")
            result = self.ai_service.analyze_page(f"获取属性 {attr_name}: {p.target}")
            return result
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_not_none)
    
    # ==================== 动作类（Action）====================
    
    def click(self, params: ActionParams) -> ActionResult:
        """点击元素"""
        def try_dom(p):
            self.page.wait_for_selector(p.target, state="visible", timeout=p.timeout * 1000)
            el = self.page.query_selector(p.target)
            if el:
                el.click()
                return True
            return False
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            screenshot_np = self._get_screenshot_for_ocr()
            coord = self.vision.find_text(p.target, screenshot_np)
            if coord:
                self.vision.find_text_and_click(p.target)
                return True
            return False
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"点击元素: {p.target}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    def input_text(self, params: ActionParams) -> ActionResult:
        """输入文本"""
        def try_dom(p):
            self.page.wait_for_selector(p.target, state="visible", timeout=p.timeout * 1000)
            self.page.fill(p.target, str(p.value))
            return True
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            screenshot_np = self._get_screenshot_for_ocr()
            coord = self.vision.find_text(p.target, screenshot_np)
            if coord:
                import pyautogui
                pyautogui.click(coord[0], coord[1])
                self._smart_sleep(300, 500)
                pyautogui.typewrite(str(p.value), interval=0.05)
                return True
            return False
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"输入文本 '{p.value}' 到: {p.target}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    def clear_input(self, params: ActionParams) -> ActionResult:
        """清空输入框"""
        def try_dom(p):
            self.page.wait_for_selector(p.target, state="visible", timeout=p.timeout * 1000)
            self.page.fill(p.target, "")
            return True
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            screenshot_np = self._get_screenshot_for_ocr()
            coord = self.vision.find_text(p.target, screenshot_np)
            if coord:
                import pyautogui
                pyautogui.click(coord[0], coord[1])
                self._smart_sleep(200, 400)
                pyautogui.hotkey('ctrl', 'a')
                self._smart_sleep(100, 200)
                pyautogui.press('delete')
                return True
            return False
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"清空输入框: {p.target}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    def scroll(self, params: ActionParams) -> ActionResult:
        """滚动页面"""
        def try_dom(p):
            direction = p.extra.get("direction", "down")
            distance = p.extra.get("distance", 500)
            scroll_map = {
                "down": (0, distance),
                "up": (0, -distance),
                "left": (-distance, 0),
                "right": (distance, 0),
            }
            dx, dy = scroll_map.get(direction, (0, distance))
            self.page.mouse.wheel(dx, dy)
            return True
        
        def try_ocr(p):
            try:
                return self.try_dom(p)
            except Exception:
                raise Exception("OCR不支持滚动")
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"滚动页面: {p.extra}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    def hover(self, params: ActionParams) -> ActionResult:
        """悬停在元素上"""
        def try_dom(p):
            self.page.wait_for_selector(p.target, state="visible", timeout=p.timeout * 1000)
            el = self.page.query_selector(p.target)
            if el:
                el.hover()
                return True
            return False
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            screenshot_np = self._get_screenshot_for_ocr()
            coord = self.vision.find_text(p.target, screenshot_np)
            if coord:
                import pyautogui
                pyautogui.moveTo(coord[0], coord[1])
                return True
            return False
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"悬停在元素上: {p.target}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    def upload_file(self, params: ActionParams) -> ActionResult:
        """上传文件"""
        def try_dom(p):
            self.page.wait_for_selector(p.target, state="visible", timeout=p.timeout * 1000)
            el = self.page.query_selector(p.target)
            if el:
                el.set_input_files(str(p.value))
                return True
            return False
        
        def try_ocr(p):
            raise Exception("OCR不支持文件上传")
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"上传文件: {p.value}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    # ==================== 键盘交互 ====================
    
    def press_key(self, params: ActionParams) -> ActionResult:
        """按键"""
        def try_dom(p):
            self.page.keyboard.press(str(p.value))
            return True
        
        def try_ocr(p):
            try:
                return self.try_dom(p)
            except Exception:
                raise Exception("OCR不支持按键")
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"按键: {p.value}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    def hotkey(self, params: ActionParams) -> ActionResult:
        """组合键"""
        def try_dom(p):
            keys = p.value if isinstance(p.value, list) else [p.value]
            for key in keys:
                self.page.keyboard.down(key)
            for key in reversed(keys):
                self.page.keyboard.up(key)
            return True
        
        def try_ocr(p):
            try:
                return self.try_dom(p)
            except Exception:
                raise Exception("OCR不支持组合键")
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"组合键: {p.value}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    def focus_element(self, params: ActionParams) -> ActionResult:
        """聚焦元素"""
        def try_dom(p):
            self.page.wait_for_selector(p.target, state="visible", timeout=p.timeout * 1000)
            el = self.page.query_selector(p.target)
            if el:
                el.focus()
                return True
            return False
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            screenshot_np = self._get_screenshot_for_ocr()
            coord = self.vision.find_text(p.target, screenshot_np)
            if coord:
                import pyautogui
                pyautogui.click(coord[0], coord[1])
                return True
            return False
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"聚焦元素: {p.target}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    # ==================== 控制类（Control）====================
    
    def wait_for(self, params: ActionParams) -> ActionResult:
        """等待条件"""
        def try_dom(p):
            condition = p.extra.get("condition", "visible")
            state_map = {
                "visible": "visible",
                "exists": "attached",
                "clickable": "visible",
                "disappear": "hidden",
            }
            state = state_map.get(condition, "visible")
            if condition == "disappear":
                try:
                    self.page.wait_for_selector(p.target, state="hidden", timeout=p.timeout * 1000)
                    return True
                except Exception:
                    return False
            else:
                self.page.wait_for_selector(p.target, state=state, timeout=p.timeout * 1000)
                return True
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            screenshot_np = self._get_screenshot_for_ocr()
            coord = self.vision.find_text(p.target, screenshot_np)
            return coord is not None
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"等待条件: {p.target}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    def switch_context(self, params: ActionParams) -> ActionResult:
        """切换上下文"""
        def try_dom(p):
            context_type = p.extra.get("type", "iframe")
            value = p.extra.get("value", "")
            if context_type == "iframe":
                frame = self.page.frame(name=value) or self.page.frame(url=value)
                if frame:
                    return frame
                return None
            elif context_type == "tab":
                pages = self.page.context.pages
                if pages:
                    return pages[-1]
                return None
            elif context_type == "window":
                return self.page
            return None
        
        def try_ocr(p):
            raise Exception("OCR不支持切换上下文")
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"切换上下文: {p.extra}")
            return result
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_not_none)
    
    def refresh_page(self, params: ActionParams) -> ActionResult:
        """刷新页面"""
        def try_dom(p):
            self.page.reload(wait_until="domcontentloaded", timeout=p.timeout * 1000)
            return True
        
        def try_ocr(p):
            try:
                return self.try_dom(p)
            except Exception:
                raise Exception("OCR不支持刷新页面")
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page("刷新页面")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
    
    def handle_popup(self, params: ActionParams) -> ActionResult:
        """处理弹窗"""
        def try_dom(p):
            action = p.extra.get("action", "accept")
            close_selectors = [
                "[class*='close']",
                "[class*='cancel']",
                "[aria-label='关闭']",
                "[aria-label='Close']",
                "button[class*='close-btn']",
            ]
            for selector in close_selectors:
                try:
                    el = self.page.query_selector(selector)
                    if el and el.is_visible():
                        if action == "accept":
                            el.click()
                            return True
                        elif action == "dismiss":
                            el.click()
                            return True
                except Exception:
                    continue
            return False
        
        def try_ocr(p):
            if not self._is_ocr_available():
                raise Exception("OCR不可用")
            action = p.extra.get("action", "accept")
            keywords = ["关闭", "取消", "不再提示", "忽略", "跳过", "Close", "Cancel", "Dismiss"]
            screenshot_np = self._get_screenshot_for_ocr()
            for keyword in keywords:
                coord = self.vision.find_text(keyword, screenshot_np)
                if coord:
                    self.vision.find_text_and_click(keyword)
                    return True
            return False
        
        def try_llm(p):
            if not self._is_ai_available():
                raise Exception("AI服务不可用")
            result = self.ai_service.analyze_page(f"处理弹窗: {p.extra}")
            return "成功" in result or "success" in result.lower()
        
        return execute_with_fallback(params, try_dom, try_ocr, try_llm, verify_true)
