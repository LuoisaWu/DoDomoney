# Scripts

项目根目录已经提供 Windows 一键启动脚本：

- `start-api.bat`：启动 FastAPI 后端，并在首次运行时创建 `.venv`、安装 Python 依赖。
- `start-desktop.bat`：启动 Electron 桌面端，并在首次运行时安装 npm 依赖。
- `start-all.bat`：同时打开后端和桌面端两个开发窗口。

后续可以继续在这个目录补充开发辅助脚本，例如：

- 初始化数据库。
- 生成演示数据。
- 导出 OpenAPI 类型。
- 打包桌面应用。
