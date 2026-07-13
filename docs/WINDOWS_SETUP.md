# Windows 开发环境启动说明

这份文档给小组成员第一次运行 Dodomoney 使用。项目是桌面软件，由后端 API 和 Electron 桌面端两部分组成，开发时需要两个进程同时运行。

## 需要先安装

- Git
- Node.js 20 或更高版本
- Python 3.11 或更高版本
- npm

如果 `git` 命令不可用，但本机已经安装 Git，可以把 Git 的 `cmd` 目录加入环境变量。例如：

```text
D:\Wujialu\下载\Git\Git\cmd
```

## 一键启动

在项目根目录双击或执行：

```bat
start-all.bat
```

它会打开两个命令行窗口：

- `Dodomoney API`：后端服务，默认地址是 `http://127.0.0.1:8000`
- `Dodomoney Desktop`：Electron 桌面端

两个窗口都不要关闭。关闭任意一个，软件对应部分就会停止。

## 分开启动

如果只想启动后端：

```bat
start-api.bat
```

如果只想启动桌面端：

```bat
start-desktop.bat
```

## 首次运行时脚本会做什么

`start-api.bat` 会检查 `apps\api\.venv` 是否存在。不存在时自动创建 Python 虚拟环境，并安装 `requirements.txt` 中的后端依赖。

`start-desktop.bat` 会检查 `apps\desktop\node_modules` 是否存在。不存在时自动执行 `npm install`，并临时设置 Electron 国内镜像：

```bat
ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
```

## 验证后端是否正常

后端窗口出现下面内容代表启动成功：

```text
Uvicorn running on http://127.0.0.1:8000
```

也可以在浏览器打开：

```text
http://127.0.0.1:8000/health
```

看到 `{"status":"ok"}` 或类似 JSON 结果，就说明后端正常。

## 常见问题

### 桌面端显示 Failed to fetch

通常是后端没有启动，或者后端启动失败。先确认后端窗口里有：

```text
Uvicorn running on http://127.0.0.1:8000
```

如果后端日志里出现 `OPTIONS ... 400 Bad Request`，说明 CORS 配置没有生效。请先拉取最新代码，然后重启后端。

### PowerShell 提示不能运行 Activate.ps1

可以不用 PowerShell 激活脚本。本项目的一键启动使用 `.bat`，不会依赖 `Activate.ps1`，直接运行：

```bat
start-api.bat
```

### Electron 下载超时

进入桌面端目录后手动设置镜像再安装：

```bat
cd apps\desktop
set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
npm install
```

### pip 提示 sse-starlette 和 starlette 冲突

当前项目没有使用 `sse-starlette`。如果是在项目虚拟环境中出现该提示，可以执行：

```bat
cd apps\api
.\.venv\Scripts\activate.bat
pip uninstall sse-starlette -y
pip install -r requirements.txt
```

## 日常开发建议

- 后端接口改动后，先确认 `http://127.0.0.1:8000/health` 可访问。
- 前端依赖变更后，组员需要重新执行 `npm install`。
- 后端依赖变更后，组员需要重新执行 `pip install -r requirements.txt`。
- 提交代码前建议运行：

```bat
cd apps\desktop
npm run build
```

```bat
cd apps\api
.\.venv\Scripts\activate.bat
python -m compileall -q app
```
