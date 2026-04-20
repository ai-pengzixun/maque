#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源管理模块，用于加载和管理UI资源文件
"""

import os
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt

# 默认资源文件夹路径
DEFAULT_RESOURCE_FOLDER = os.path.dirname(__file__)
# 自定义资源文件夹路径列表
CUSTOM_RESOURCE_FOLDERS = []


def get_resource_path(path):
    """
    获取资源文件的完整路径
    
    Args:
        path: 资源文件的相对路径或文件名
        
    Returns:
        str: 资源文件的完整路径，如果文件不存在则返回None
    """
    if not isinstance(path, str):
        raise TypeError("Input argument 'path' should be str type, " "but get {}".format(type(path)))
    
    # 搜索路径列表
    search_paths = ["", DEFAULT_RESOURCE_FOLDER] + CUSTOM_RESOURCE_FOLDERS
    
    # 尝试在每个搜索路径中查找文件
    for prefix in search_paths:
        full_path = os.path.join(prefix, path)
        if os.path.isfile(full_path):
            return full_path
    
    # 尝试在子目录中查找
    for prefix in search_paths:
        for root, dirs, files in os.walk(prefix):
            for file in files:
                if file == path:
                    return os.path.join(root, file)
    
    return None


class ResourceCache:
    """资源缓存类，用于缓存已加载的资源"""
    
    def __init__(self, cls):
        """
        初始化资源缓存
        
        Args:
            cls: 资源类，如QPixmap或QIcon
        """
        self.cls = cls
        self._cache = {}
    
    def __call__(self, path, color=None):
        """
        获取资源
        
        Args:
            path: 资源文件路径
            color: 颜色（可选）
            
        Returns:
            cls: 资源实例
        """
        full_path = get_resource_path(path)
        if full_path is None:
            return self.cls()
        
        key = "{}{}".format(full_path.lower(), color or "")
        if key not in self._cache:
            if full_path.endswith(".svg"):
                # 处理SVG文件
                from PySide6.QtSvg import QSvgRenderer
                from PySide6.QtCore import QByteArray
                
                renderer = QSvgRenderer()
                with open(full_path, "r") as f:
                    data_content = f.read()
                    if color is not None:
                        data_content = data_content.replace("#555555", color)
                    renderer.load(QByteArray(data_content.encode()))
                    
                pix = QPixmap(128, 128)
                pix.fill(Qt.transparent)
                
                from PySide6.QtGui import QPainter
                painter = QPainter(pix)
                renderer.render(painter)
                painter.end()
                
                if self.cls is QPixmap:
                    self._cache[key] = pix
                else:
                    self._cache[key] = self.cls(pix)
            else:
                # 处理其他类型的文件
                self._cache[key] = self.cls(full_path)
        
        return self._cache[key]


# 创建全局资源实例
RPixmap = ResourceCache(QPixmap)
RIcon = ResourceCache(QIcon)

# ── 字体图标支持 ─────────────────────────────────────────────────────────── #
from PySide6.QtGui import QFont, QFontDatabase

# 加载 Material Icons 字体
def load_material_icons():
    """加载 Material Icons 字体"""
    font_path = get_resource_path("fonts/MaterialIcons-Regular.ttf")
    if font_path:
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            return True
    return False

# 确保字体加载
load_material_icons()

class RFont(QFont):
    """字体资源类"""
    def __init__(self, family="Material Icons", size=16):
        super().__init__(family, size)

# 常用 Material Icons 图标 Unicode
# 编码查询页面 https://fonts.google.com/icons
MATERIAL_ICONS = {
    "remove": "\uE15B",        # 最小化
    "fullscreen": "\uE5D0",  # 最大化
    "close": "\uE5CD",          # 还原
    "close_fullscreen": "\uF1CF",  # 关闭
    "logout": "\uE9BA",          # 退出
   }
