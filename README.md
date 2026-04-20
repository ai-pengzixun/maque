# Maque（麻雀）

## 简介
Maque（麻雀）是一款面向脚本类智能体的轻量化本地化桌面底座，以麻雀虽小、五脏俱全为设计理念，在轻量体积下提供完整的 AI 自动化能力。
- **分级智能执行：** 采用 DOM 优先、OCR 兜底、LLM 决策的三级 fallback 机制，兼顾执行效率与复杂场景适配性。
- **本地优先部署：** 支持网关互联与本地化运行，数据隐私可控，适配各类智能体生态接入。
- **降本增效设计：** 内置 OCR 与 LLM 能力，规划集成 MiniLLM，大幅降低云端大模型 Token 消耗。
- **轻量完备底座：** 体积精简、能力齐全，为桌面端脚本智能体提供稳定可靠的运行基座。


## 技术栈

- **GUI:** PySide6 (界面)
- **Automation:** Robot Framework (逻辑编排), Playwright (Web 执行)
- **System Control:** PyAutoGUI (OS 级控制)
- **Vision:** PaddleOCR (图像/文字识别)
- **Database:** MySQL (用户与任务持久化)

## 项目结构

```
jianrujiajing-client/
├── run.py                  # 主入口文件
├── setup.py                # 依赖管理
├── README.md               # 项目说明
├── agents/                 # 智能体目录
├── data/                   # 数据存储目录
│   ├── errors/             # 错误截图
│   ├── robot_output/       # Robot Framework 输出
│   ├── task_history/       # 任务历史
│   └── video_records/      # 视频记录
└── src/
    ├── main_window.py      # 主窗口
    ├── logging_system.py   # 日志系统
    ├── task_thread.py      # 任务线程
    ├── robot_runner.py     # Robot Framework 运行器
    ├── browser_manager.py  # 浏览器管理器
    ├── human_controller.py # 拟人化控制器
    ├── vision_recognition.py # 视觉识别
    ├── network/            # 网络通信模块
    ├── storage/            # 存储模块
    ├── updater/            # 应用更新模块
    └── ui/
        ├── components/     # UI组件
        │   ├── sidebar.py  # 侧边栏
        │   ├── main_content.py  # 主显示区
        │   └── agents.py   # 智能体管理
        └── resources/      # UI资源
            ├── images/     # 图片资源
            └── svg/        # SVG资源
```

## 核心功能

1. **基于 QObject 和 Signal 的全局日志转发器**
   - 支持不同级别的日志（info、warning、error、debug）
   - 自动格式化日志消息，添加时间戳
   - 通过 Signal 机制实现日志事件的发送
2. **主界面布局**
   - 左侧导航栏：包含任务列表、日志查看、环境设置按钮
   - 右侧主显示区：包含日志查看器和测试连接按钮
   - 采用响应式布局，界面美观大方
3. **拟人化模拟**
   - 使用 `random.uniform()` 实现随机延迟
   - 模拟人类操作的不确定性
4. **异常处理**
   - 捕获并处理任务执行过程中的异常
   - 将错误信息映射到日志系统

## 安装步骤

1. **安装依赖**
   ```bash
   # 安装 PySide6
   pip install PySide6

   # 安装其他依赖
   pip install robotframework playwright pyautogui paddleocr
   ```
2. **安装项目**
   ```bash
   # 进入项目目录
   cd ~\jianrujiajing-client

   # 安装项目（开发模式）
   pip install -e .
   ```

## 使用方法

1. **启动程序**
   ```bash
   python run.py
   ```
2. 代码规范

本项目严格遵守以下代码规范：

1. **模块化**：采用 Service-Logic-UI 三层架构
2. **并发处理**：使用 QThread 进行任务执行，Signal/Slot 进行通信
3. **拟人化模拟**：使用随机延迟模拟人类操作
4. **异常处理**：包含 try-except 捕获异常
5. **命名规范**：遵循 PEP 8 规范
6. **类型注解**：所有函数都包含类型提示

## 编译打包

### 使用 PyInstaller 打包

1. **安装 PyInstaller**
   ```bash
   pip install pyinstaller
   ```
2. **创建打包配置文件**
   - 在项目根目录创建 `pyinstaller.spec` 文件
   - 配置文件内容示例：
     ```python
     # pyinstaller.spec

     a = Analysis(
         ['run.py'],
         pathex=['.'],
         binaries=[],
         datas=[
             ('agents', 'agents'),
             ('data', 'data'),
             ('src/ui/resources', 'src/ui/resources')
         ],
         hiddenimports=[
             'paddleocr',
             'playwright',
             'robotframework'
         ],
         hookspath=[],
         runtime_hooks=[],
         excludes=[],
         win_no_prefer_redirects=False,
         win_private_assemblies=False,
         cipher=None,
         noarchive=False
     )

     pyz = PYZ(a.pure, a.zipped_data, cipher=None)

     exe = EXE(
         pyz,
         a.scripts,
         a.binaries,
         a.zipfiles,
         a.datas,
         [],
         name='Maque Client',
         debug=False,
         bootloader_ignore_signals=False,
         strip=False,
         upx=True,
         upx_exclude=[],
         runtime_tmpdir=None,
         console=True
     )
     ```
3. **执行打包命令**
   ```bash
   pyinstaller pyinstaller.spec
   ```
4. **打包结果**
   - 打包后的可执行文件会在 `dist` 目录中
   - 包含所有依赖和资源文件

### 注意事项

- 打包过程可能需要较长时间，特别是第一次打包
- 打包后的可执行文件体积较大，因为包含了所有依赖
- 运行前请确保目标机器已安装必要的系统依赖

## 许可证

本项目采用 Apache-2.0 许可证。

### Dependencies License
Maque uses the following open-source libraries:
- robotframework: Apache-2.0
- playwright: Apache-2.0
- paddleocr: Apache-2.0

## 致谢

本项目来源于令牌时代公司，是商用系统 **渐入佳境** 的开源版

## 联系方式

如有问题或建议，请联系项目维护者
