# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
用于将佳境智能体管理客户端打包为可执行文件
"""

import os
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE

# 项目根目录（使用SPECPATH变量，这是PyInstaller提供的spec文件所在目录）
project_root = os.path.abspath(SPECPATH)

# 应用版本号
APP_VERSION = "1.0.0"

# 应用名称
APP_NAME = "佳境智能体管理"

# 应用图标
icon_path = os.path.join(project_root, "src", "ui", "resources", "images", "logo_32.png")

# 需要包含的数据文件
datas = [
    # UI资源文件
    (os.path.join(project_root, "src", "ui", "resources"), "src/ui/resources"),
    # 智能体目录
    (os.path.join(project_root, "agents"), "agents"),
]

# 需要包含的隐藏导入
hiddenimports = [
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "robotframework",
    "requests",
    "paddleocr",
    "pyautogui",
    "playwright",
    "src.main_window",
    "src.robot_runner",
    "src.logging_system",
    "src.browser_manager",
    "src.human_controller",
    "src.vision_recognition",
    "src.task_thread",
    "src.network.http_client",
    "src.network.file_downloader",
    "src.storage.database",
    "src.updater.updater",
    "src.ui.components.sidebar",
    "src.ui.components.main_content",
    "src.ui.components.agents",
    "src.ui.components.tasks",
    "src.ui.components.log",
    "src.ui.components.config",
]

# 二进制文件
binaries = []

# 排除的模块
excludes = [
    "matplotlib",
    "numpy.random._examples",
    "scipy",
    "pandas",
    "tkinter",
    "unittest",
    "pydoc",
    # "email",  # pkg_resources依赖此模块，不能排除
    # "http",   # requests等库依赖此模块，不能排除
    # "xml",    # 可能被依赖，不排除
    # "xmlrpc", # 可能被依赖，不排除
]

block_cipher = None

a = Analysis(
    [os.path.join(project_root, "run.py")],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 单文件模式
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if os.path.exists(icon_path) else None,
    version_info={
        'version': APP_VERSION,
        'company_name': '佳境智能',
        'file_description': '佳境智能体管理客户端',
        'internal_name': 'jianrujiajing-client',
        'legal_copyright': 'Copyright (C) 2025 佳境智能',
        'original_filename': f'{APP_NAME}.exe',
        'product_name': APP_NAME,
    },
)
