#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目依赖管理
"""

from setuptools import setup, find_packages


setup(
    name="jianrujiajing-client",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PySide6",
        "robotframework",
        "playwright",
        "pyautogui",
        "paddleocr",
        "pytesseract",
        "opencv-python",
        "Pillow"
    ],
    entry_points={
        "console_scripts": [
            "rpa-client = run:main"
        ]
    }
)