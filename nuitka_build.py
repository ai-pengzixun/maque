#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuitka 打包配置脚本
用于将佳境智能体管理客户端打包为可执行文件
"""

import os
import sys
import subprocess


def get_nuitka_command():
    """获取Nuitka打包命令配置"""
    
    # 项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 应用版本号
    APP_VERSION = "1.0.0"
    
    # 应用名称
    APP_NAME = "佳境智能体管理"
    
    # 图标路径
    icon_path = os.path.join(project_root, "src", "ui", "resources", "images", "logo_32.png")
    
    # 构建基础命令
    cmd = [
        sys.executable, "-m", "nuitka",
        
        # 基本选项
        "--standalone",                    # 生成独立可执行文件
        "--windows-console-mode=attach",  # 不显示控制台窗口
        
        # 编译器选择（二选一）
        "--mingw64",                       # 使用MinGW64（需要下载）
        # "--msvc=latest",                   # 使用MSVC（如果已安装Visual Studio）
        
        # 性能优化（可选）
        # "--lto=yes",                       # 启用链接时优化（编译更慢，运行更快）
        "--jobs=4",                        # 并行编译作业数
        
        # 单文件模式（可选，取消注释启用）
        # "--onefile",                       # 打包成单个exe文件
        
        # 插件
        "--enable-plugin=pyside6",         # 启用PySide6插件（必须）
        
        # 图标
        f"--windows-icon-from-ico={icon_path}",
        
        # 需要包含的包和模块
        "--include-package=src",
        "--include-package=src.ui",
        "--include-package=src.ui.components",
        "--include-package=src.ui.resources",
        "--include-package=src.network",
        "--include-package=src.storage",
        "--include-package=src.updater",
        
        # 需要包含的数据目录
        f"--include-data-dir={os.path.join(project_root, 'src', 'ui', 'resources')}=src/ui/resources",
        f"--include-data-dir={os.path.join(project_root, 'agents')}=agents",
        
        # Windows版本信息
        f"--windows-company-name=佳境智能",
        f"--windows-product-name={APP_NAME}",
        f"--windows-file-version={APP_VERSION}",
        f"--windows-product-version={APP_VERSION}",
        f"--windows-file-description=佳境智能体管理客户端",
        
        # 输出配置
        "--output-dir=dist",
        f"--output-filename={APP_NAME}",
        
        # 主程序入口
        "run.py"
    ]
    
    return cmd


def build():
    """执行打包"""
    cmd = get_nuitka_command()
    
    print("=" * 60)
    print("佳境智能体管理客户端 - Nuitka 打包")
    print("=" * 60)
    print(f"\n执行命令:\n{' '.join(cmd)}\n")
    print("=" * 60)
    
    # 执行命令
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    if result.returncode == 0:
        print("\n✅ 打包成功！")
        print(f"输出目录: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')}")
    else:
        print(f"\n❌ 打包失败，返回码: {result.returncode}")
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(build())
