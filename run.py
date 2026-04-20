#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPA 执行端主入口
"""

import sys
import os

# 获取应用程序所在目录（打包后exe所在目录）
if getattr(sys, 'frozen', False):
    # 打包后的应用
    app_dir = os.path.dirname(sys.executable)
    # 添加应用目录到Python路径
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    # 设置工作目录
    os.chdir(app_dir)

try:
    from PySide6.QtWidgets import QApplication
    from src.main_window import MainWindow
except Exception as e:
    import traceback
    error_msg = f"导入模块失败: {e}\n{traceback.format_exc()}"
    print(error_msg, file=sys.stderr)
    input("按Enter键退出...")
    sys.exit(1)


def main():
    """主函数"""
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        error_msg = f"启动应用失败: {e}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        input("按Enter键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
