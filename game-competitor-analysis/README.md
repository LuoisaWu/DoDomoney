# 基于 AI 辅助的多平台游戏竞品动态追踪与智能对标分析系统

## 第一阶段简介

本阶段提供一个可独立运行的后端最小版本。系统使用 FastAPI 提供接口，以 SQLite 保存游戏数据，并通过规则匹配目标游戏、计算竞品相似度、生成市场定位、SWOT 和策略建议。当前分析内容由本地模板生成，不调用真实大模型。

内置数据覆盖 Steam 和 Switch，共 12 款游戏。应用首次启动时会自动从 `backend/data/games.json` 创建并填充 `backend/game_analysis.db`。

## 后端启动方式

项目已在仓库根目录的 `.venv` 中创建 Python 3.11 环境。在 PowerShell 中执行：

```powershell
cd C:\Users\12838\GameScope
.\.venv\Scripts\Activate.ps1
pip install -r .\game-competitor-analysis\backend\requirements.txt
cd .\game-competitor-analysis\backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：

- API 地址：http://127.0.0.1:8000
- Swagger 文档：http://127.0.0.1:8000/docs
- ReDoc 文档：http://127.0.0.1:8000/redoc

## 接口说明

| 方法 | 路径 | 功能 |
|---|---|---|
| GET | `/api/games` | 返回全部游戏 |
| GET | `/api/games/{game_id}` | 返回指定游戏详情，不存在时返回 404 |
| POST | `/api/chat` | 匹配目标游戏并生成竞品分析 |

## 前端功能与启动方式

第二阶段提供基于 Vue 3、Element Plus 与 ECharts 的单页数据分析看板，包含：

- 对话式游戏竞品分析与快捷示例问题
- 目标游戏信息画像与竞品推荐表格
- 游戏概况、竞品对比与市场定位洞察
- SWOT 四象限和三项策略建议
- 竞品相似度、评分、好评率与平台分布图表

确保后端保持运行，再打开一个新的 PowerShell 窗口执行：

```powershell
cd C:\Users\12838\GameScope\game-competitor-analysis\frontend
npm install
npm run dev
```

前端默认访问地址为 http://127.0.0.1:5173 。前端请求的后端地址配置在 `frontend/src/api.js`，默认为 http://127.0.0.1:8000 。

## 示例请求

PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/games
Invoke-RestMethod http://127.0.0.1:8000/api/games/1

$body = @{ query = "分析 Stardew Valley 的竞品" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/chat -ContentType "application/json" -Body $body
```

也可直接在 Swagger 的 `/docs` 页面展开接口，点击 **Try it out** 后发送请求。

可测试的问题包括：

- `分析 Stardew Valley 的竞品`
- `Hades 和同类游戏相比怎么样？`
- `帮我看看 zelda tears of kingdom 的市场定位`
- `推荐一个评分高的游戏并分析竞品`（无法匹配名称时测试默认回退）

## 后续开发计划

1. 接入 Steam、Nintendo 等平台的数据采集和定时更新。
2. 引入真实大模型，增强自然语言理解与分析文本质量。
3. 开发前端可视化看板、筛选搜索和竞品对比图表。
4. 增加用户配置、追踪列表、告警和历史趋势。
5. 支持 PDF、Word 等分析报告导出。
