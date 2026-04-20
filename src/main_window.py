#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QProgressDialog, QDialog, QLabel, QVBoxLayout as QVLayout,
    QTextEdit, QPushButton as QBtn, QApplication, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QColor
import os
import sys
import json
from src.ui.components.sidebar import Sidebar
from src.ui.components.main_content import MainContent
from src.task_thread import TestTaskThread
from src.logging_system import Logger
from src.jjrj_config import JjrjConfig


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 类变量：当前登录用户信息，全局可访问
    current_user = None  # 格式: {"username": str, "nickname": str, "rolename": str, "avatar": str}
    user_data_dir = None  # 用户数据目录路径，格式: user_data_{username}

    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), "ui", "resources", "images", "logo_32.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("佳境智能体管理")
        self.setGeometry(100, 100, 1280, 720)
        
        # 用于窗口拖动的变量
        self._drag_pos = None
        
        # 初始化日志系统
        self.logger = Logger()
        
        # 延迟初始化 Robot Runner，避免启动时加载 paddlepaddle
        self.robot_runner = None
        
        # 更新器
        self.updater = None
        self.progress_dialog = None
        
        # 先检查登录状态
        if not self._check_and_do_login():
            # 用户取消登录或登录失败，退出应用
            self.logger.info("登录失败或用户取消，程序即将退出")
            QApplication.quit()
            sys.exit(0)
        
        # 初始化用户数据目录和数据库
        self._init_user_data()
        
        # 创建UI
        self._init_ui()
        
        # 检查更新
        QTimer.singleShot(1000, self._check_update)
    
    def _check_and_do_login(self) -> bool:
        """检查登录状态，如未登录则显示登录对话框
        
        Returns:
            bool: 是否成功登录
        """
        from src.ui.components.login import check_login_status, show_login_dialog
        
        is_logged_in, user_info = check_login_status()
        
        if is_logged_in:
            # 已登录，设置全局用户信息
            MainWindow.current_user = user_info
            MainWindow.user_data_dir = f"user_data_{user_info.get('username', 'default')}"
            
            # 设置全局配置
            JjrjConfig.set_current_user(user_info)
            
            self.logger.info(f"用户已登录: {user_info.get('nickname', user_info.get('username'))}")
            return True
        else:
            # 未登录，显示登录对话框
            self.logger.info("用户未登录，显示登录界面")
            success, user_info = show_login_dialog(self)
            
            if success:
                # 登录成功，设置全局用户信息
                MainWindow.current_user = user_info
                MainWindow.user_data_dir = f"user_data_{user_info.get('username', 'default')}"
                
                # 设置全局配置
                JjrjConfig.set_current_user(user_info)
                
                self.logger.info(f"用户登录成功: {user_info.get('nickname', user_info.get('username'))}")
                return True
            else:
                # 用户取消登录
                self.logger.info("用户取消登录")
                return False
    
    def _init_user_data(self):
        """初始化用户数据目录和数据库"""
        try:
            username = JjrjConfig.get_username()
            
            # 确保用户数据目录存在
            user_data_dir = JjrjConfig.ensure_user_data_dir()
            self.logger.info(f"用户数据目录已创建/确认: {user_data_dir}")
            
            # 初始化数据库
            db_conn = JjrjConfig.init_user_database(username)
            db_conn.close()
            self.logger.info(f"用户数据库已初始化: {JjrjConfig.get_user_db_path(username)}")
            
        except Exception as e:
            self.logger.error(f"初始化用户数据失败: {e}")
    
    def _init_ui(self):
        """初始化UI（在登录成功后调用）"""
        # 设置主窗口为无边框并添加阴影效果
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局（为阴影预留空间）
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(0)
        
        # 创建带阴影和圆角的容器
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 90))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)
        
        # 确保阴影效果正确应用
        container.ensurePolished()
        container.update()
        
        # 容器内部布局
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 标题栏（包含窗口控制按钮）
        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet("background-color: transparent;")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(16, 0, 16, 0)
        title_bar_layout.setSpacing(8)
        
        # 窗口标题
        title_label = QLabel("佳境智能体管理")
        title_label.setStyleSheet("font-size: 14px; font-weight: 500; color: rgba(0,0,0,0.85);")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        
        # 导入 Material Icons
        from src.ui.resources.resource_manager import MATERIAL_ICONS
        
        # 最小化按钮
        min_btn = QPushButton(MATERIAL_ICONS["remove"])
        min_btn.setFixedSize(32, 32)
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(0,0,0,0.45);
                border: none;
                border-radius: 4px;
                font-family: 'Material Icons';
                font-size: 20px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.06);
                color: rgba(0,0,0,0.85);
            }
        """)
        min_btn.clicked.connect(self.showMinimized)
        title_bar_layout.addWidget(min_btn)
        
        # 最大化/还原按钮
        self.max_btn = QPushButton(MATERIAL_ICONS["fullscreen"])
        self.max_btn.setFixedSize(32, 32)
        self.max_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(0,0,0,0.45);
                border: none;
                border-radius: 4px;
                font-family: 'Material Icons';
                font-size: 20px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.06);
                color: rgba(0,0,0,0.85);
            }
        """)
        self.max_btn.clicked.connect(self._toggle_maximize)
        title_bar_layout.addWidget(self.max_btn)
        
        # 关闭按钮
        close_btn = QPushButton(MATERIAL_ICONS["close"])
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(0,0,0,0.45);
                border: none;
                border-radius: 4px;
                font-family: 'Material Icons';
                font-size: 20px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #ff4d4f;
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(close_btn)
        
        container_layout.addWidget(title_bar)
        
        # 主内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 左侧导航栏
        self.sidebar = Sidebar()
        content_layout.addWidget(self.sidebar, 1)
        
        # 右侧主显示区
        self.main_content = MainContent()
        content_layout.addWidget(self.main_content, 4)
        
        container_layout.addWidget(content_widget, 1)
        
        # 将容器添加到主布局
        main_layout.addWidget(container)
        
        # 连接信号
        self.logger.log_signal.connect(self.main_content.log_viewer.append_log)
        
        # 连接侧边栏按钮点击事件
        button_configs = {
            "task_list": (self.main_content.show_task_list, "切换到任务列表界面"),
            "log_view": (self.main_content.show_log_view, "切换到日志查看界面"),
            "agent_management": (self.main_content.show_agent_management, "切换到智能管理界面"),
            "settings": (self.main_content.show_env_settings, "切换到环境设置界面")
        }
        
        for button_id, (show_func, log_message) in button_configs.items():
            button = self.sidebar.get_button(button_id)
            if button:
                button.clicked.connect(lambda checked, bid=button_id, sf=show_func, lm=log_message: self._on_menu_clicked(bid, sf, lm))
        
        # 动态加载智能体
        self.agents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")
        self.load_agents()
        
        # 连接刷新按钮
        self.main_content.agent_management_ui.refresh_button.clicked.connect(self.load_agents)
        
        # 默认显示智能体管理界面
        self.main_content.show_agent_management()
        # 更新侧边栏选中状态
        self.sidebar._update_button_state("agent_management")
        
        # 初始化 Robot Runner
        self._init_robot_runner()
    
    def _init_robot_runner(self):
        """初始化 Robot Runner"""
        if self.robot_runner is None:
            try:
                from src.robot_runner import RobotRunner
                self.robot_runner = RobotRunner()
                # 连接 Robot Runner 信号
                self.robot_runner.execution_started.connect(self.on_robot_execution_started)
                self.robot_runner.execution_ended.connect(self.on_robot_execution_ended)
                self.robot_runner.test_started.connect(self.on_robot_test_started)
                self.robot_runner.test_ended.connect(self.on_robot_test_ended)
                self.robot_runner.keyword_ended.connect(self.on_robot_keyword_ended)
                self.robot_runner.log_message.connect(self.on_robot_log_message)
                self.robot_runner.error.connect(self.on_robot_error)
                self.logger.info("Robot Runner 初始化完成")
            except Exception as e:
                self.logger.error(f"初始化 Robot Runner 失败: {str(e)}")
        
    def start_test_task(self):
        """启动测试任务"""
        self.test_thread = TestTaskThread()
        self.test_thread.start()
        self.logger.info("测试任务已启动")
    
    def start_robot_test(self):
        """启动 Robot 测试"""
        try:
            # 确保 Robot Runner 已初始化
            if self.robot_runner is None:
                self._init_robot_runner()
            self.robot_runner.set_robot_file("smoke_test.robot")
            self.robot_runner.set_output_dir("data/robot_output")
            self.robot_runner.start()
            self.logger.info("Robot 测试已启动")
        except Exception as e:
            self.logger.error(f"启动 Robot 测试失败: {str(e)}")
    
    def on_robot_execution_started(self):
        """Robot 执行开始"""
        self.logger.info("Robot 执行开始")
    
    def on_robot_execution_ended(self, status):
        """Robot 执行结束"""
        self.logger.info(f"Robot 执行结束，状态: {status}")
    
    def on_robot_test_started(self, name):
        """Robot 测试开始"""
        self.logger.info(f"测试开始: {name}")
    
    def on_robot_test_ended(self, name, status, message):
        """Robot 测试结束"""
        self.logger.info(f"测试结束: {name}, 状态: {status}")
        if message:
            # 检查消息是否已经格式化过
            if not message.startswith("["):
                self.logger.info(f"测试消息: {message}")
            else:
                self.logger.info(message)
    
    def on_robot_keyword_ended(self, name, status, message):
        """Robot 关键词结束"""
        self.logger.info(f"关键词结束: {name}, 状态: {status}")
        if message:
            # 检查消息是否已经格式化过
            if not message.startswith("["):
                self.logger.info(f"关键词消息: {message}")
            else:
                self.logger.info(message)
    
    def on_robot_log_message(self, level, msg):
        """Robot 日志消息"""
        # 直接使用原始消息，避免重复添加前缀
        # 检查消息是否已经格式化过
        if not msg.startswith("["):
            # 未格式化的消息，添加前缀
            self.logger.info(f"[{level}] {msg}")
        else:
            # 已格式化的消息，直接输出
            self.logger.info(msg)
    
    def on_robot_error(self, msg):
        """Robot 错误"""
        self.logger.error(f"Robot 错误: {msg}")
    
    def _check_update(self):
        """检查更新"""
        try:
            from src.updater import Updater
            
            self.updater = Updater()
            
            # 连接信号
            self.updater.update_available.connect(self._on_update_available)
            self.updater.update_not_needed.connect(self._on_update_not_needed)
            self.updater.update_error.connect(self._on_update_error)
            self.updater.download_progress.connect(self._on_download_progress)
            self.updater.download_completed.connect(self._on_download_completed)
            self.updater.download_failed.connect(self._on_download_failed)
            self.updater.install_completed.connect(self._on_install_completed)
            
            # 开始检查更新
            self.updater.check_update()
            
        except Exception as e:
            self.logger.error(f"初始化更新检查失败: {str(e)}")
    
    def _on_update_available(self, update_info):
        """发现可用更新"""
        try:
            version = update_info.get('version', '未知')
            is_force = update_info.get('force', False)
            is_pending = update_info.get('pending', False)
            
            from src.ui.components.update_dialog import UpdateDialog
            
            if is_pending:
                self.logger.info(f"发现待安装的更新: v{version}")
            else:
                self.logger.info(f"发现新版本: v{version}")
            
            # 显示更新对话框
            dialog = UpdateDialog(update_info, self, is_pending)
            result = dialog.exec()
            
            if dialog.user_choice == 'update':
                if is_pending:
                    # 直接安装已下载的更新
                    self._install_update(update_info.get('package_path'))
                else:
                    # 开始下载更新
                    self._start_download(update_info)
            else:
                self.logger.info("用户选择稍后更新")
                # 如果是强制更新，提示用户
                if is_force and not is_pending:
                    QMessageBox.warning(
                        self,
                        "强制更新",
                        "此版本为强制更新，建议尽快完成更新以获得更好的体验。"
                    )
                    
        except Exception as e:
            self.logger.error(f"处理更新信息失败: {str(e)}")
    
    def _on_update_not_needed(self):
        """无需更新"""
        self.logger.info("当前已是最新版本")
    
    def _on_update_error(self, error_msg):
        """更新检查错误"""
        self.logger.error(f"更新检查失败: {error_msg}")
    
    def _start_download(self, update_info):
        """开始下载更新"""
        try:
            self.logger.info("开始下载更新...")
            
            # 创建进度对话框
            self.progress_dialog = QProgressDialog("正在下载更新...", "取消", 0, 100, self)
            self.progress_dialog.setWindowTitle("下载更新")
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setValue(0)
            
            # 连接取消按钮
            self.progress_dialog.canceled.connect(self._on_download_cancelled)
            
            # 开始下载
            success = self.updater.download_update(update_info)
            if not success:
                self.progress_dialog.close()
                QMessageBox.warning(self, "下载失败", "无法启动下载，请稍后重试。")
                
        except Exception as e:
            self.logger.error(f"启动下载失败: {str(e)}")
            if self.progress_dialog:
                self.progress_dialog.close()
    
    def _on_download_progress(self, progress):
        """下载进度更新"""
        if self.progress_dialog:
            self.progress_dialog.setValue(progress)
    
    def _on_download_completed(self, package_path):
        """下载完成"""
        self.logger.info(f"更新下载完成: {package_path}")
        
        if self.progress_dialog:
            self.progress_dialog.close()
        
        # 询问用户是否立即安装
        reply = QMessageBox.question(
            self,
            "下载完成",
            "更新包已下载完成，是否立即安装？\n\n安装过程中应用将重启。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self._install_update(package_path)
        else:
            self.logger.info("用户选择稍后安装")
            QMessageBox.information(
                self,
                "提示",
                "更新包已保存，下次启动时将提示安装。"
            )
    
    def _on_download_failed(self, error_msg):
        """下载失败"""
        self.logger.error(f"下载失败: {error_msg}")
        
        if self.progress_dialog:
            self.progress_dialog.close()
        
        QMessageBox.warning(self, "下载失败", f"更新下载失败:\n{error_msg}")
    
    def _on_download_cancelled(self):
        """用户取消下载"""
        self.logger.info("用户取消下载")
        if self.updater:
            self.updater.cancel_download()
    
    def _install_update(self, package_path):
        """安装更新"""
        try:
            self.logger.info("开始安装更新...")
            
            # 显示安装中提示
            QMessageBox.information(
                self,
                "安装更新",
                "即将开始安装更新，应用将自动重启。\n\n请稍候..."
            )
            
            # 启动安装
            success = self.updater.install_update(package_path)
            if success:
                self.logger.info("安装程序已启动")
                # 退出当前应用
                self.close()
            else:
                QMessageBox.warning(self, "安装失败", "无法启动安装程序，请稍后重试。")
                
        except Exception as e:
            self.logger.error(f"安装更新失败: {str(e)}")
            QMessageBox.critical(self, "安装失败", f"安装更新时发生错误:\n{str(e)}")
    
    def _on_install_completed(self, success, message):
        """安装完成回调"""
        if success:
            self.logger.info(f"安装完成: {message}")
        else:
            self.logger.error(f"安装失败: {message}")
    
    def _on_menu_clicked(self, button_id, show_func, log_message):
        """统一处理菜单点击事件"""
        # 显示对应界面
        show_func()
        # 记录日志
        self.logger.info(log_message)
        # 更新侧边栏按钮样式
        button_configs = ["task_list", "log_view", "agent_management", "settings"]
        for bid in button_configs:
            button = self.sidebar.get_button(bid)
            if button:
                self.sidebar._update_button_style(button, bid == button_id)
    
    def load_agents(self):
        """加载智能体"""
        self.logger.info(f"开始加载智能体，目录: {self.agents_dir}")
        self.main_content.agent_management_ui.load_agents(self.agents_dir, self)
        self.logger.info("智能体加载完成")
    
    # ════════════════════════════════════════════════════════════════════════ #
    #  智能体执行方法 - 动态执行任意智能体
    # ════════════════════════════════════════════════════════════════════════ #
    def execute_agent(self, agent_path: str, robot_file: str):
        """执行指定的智能体
        
        Args:
            agent_path: 智能体目录路径
            robot_file: 智能体主文件名称（如 douyin_collector.robot）
        """
        try:
            # 获取智能体名称（从路径中提取）
            agent_name = os.path.basename(agent_path)
            self.logger.info(f"正在启动智能体: {agent_name}...")
            
            # 确保 Robot Runner 已初始化
            if self.robot_runner is None:
                self._init_robot_runner()
            
            # 设置智能体文件路径
            robot_file_path = os.path.join(agent_path, robot_file)
            
            if not os.path.exists(robot_file_path):
                self.logger.error(f"智能体文件不存在: {robot_file_path}")
                return
            
            # 设置输出目录（使用 JjrjConfig 规范化路径）
            output_dir = JjrjConfig.get_robot_output_dir()
            
            # 从 agent.json 读取输入变量
            variables = self._load_agent_variables(agent_path)
            self.logger.info(f"读取到的变量: {variables}")
            
            # 配置并启动 Robot Runner
            self.robot_runner.set_robot_file(robot_file_path)
            self.robot_runner.set_output_dir(output_dir)
            self.robot_runner.set_variables(variables)
            self.logger.info(f"Robot Runner 变量已设置: {self.robot_runner.variables}")
            self.robot_runner.start()
            
            self.logger.info(f"智能体 {agent_name} 已启动")
            
        except Exception as e:
            self.logger.error(f"启动智能体失败: {str(e)}")
    
    def _load_agent_variables(self, agent_path: str) -> dict:
        """
        从 agent.json 读取输入变量
        
        Args:
            agent_path: 智能体目录路径
            
        Returns:
            dict: 变量字典，如 {"SEARCH_KEYWORD": "渐入佳境"}
        """
        variables = {}
        try:
            agent_json_path = os.path.join(agent_path, "agent.json")
            if os.path.exists(agent_json_path):
                with open(agent_json_path, 'r', encoding='utf-8') as f:
                    agent_config = json.load(f)
                
                inputs = agent_config.get("inputs", [])
                for input_item in inputs:
                    if isinstance(input_item, dict):
                        name = input_item.get("name")
                        default = input_item.get("default", "")
                        if name:
                            variables[name] = default
                            self.logger.info(f"加载变量: {name} = {default}")
        except Exception as e:
            self.logger.warning(f"读取智能体变量失败: {str(e)}")
        
        return variables
    
    # ------------------------------------------------------------------ #
    #  窗口拖动事件
    # ------------------------------------------------------------------ #
    def mousePressEvent(self, event):
        """鼠标按下事件，记录拖动起始位置"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件，实现窗口拖动"""
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件，清除拖动位置"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
            event.accept()
    
    def _toggle_maximize(self):
        """切换窗口最大化/还原状态"""
        from src.ui.resources.resource_manager import MATERIAL_ICONS
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setText(MATERIAL_ICONS["fullscreen"])
        else:
            self.showMaximized()
            self.max_btn.setText(MATERIAL_ICONS["close_fullscreen"])
