# Dodomoney 架构说明

## 总体分层

```text
Electron 桌面壳
  └─ React Renderer
      └─ API Client
          └─ FastAPI Routers
              └─ Services
                  └─ Repositories
                      └─ SQLite
```

## 为什么这样设计

Dodomoney 后续会包含自然语言处理、图片识别、预算分析、个性化角色、分类学习等模块。如果只做一个前端页面，后续很难维护。因此当前框架把项目拆成三个稳定边界：

- `apps/desktop`：只关心桌面体验、页面状态和用户交互。
- `apps/api`：处理业务逻辑、数据持久化、AI 编排和统计计算。
- `shared`：放置前后端共同遵守的分类、接口契约和类型说明。

## 后端模块

- `api/routes`：HTTP 接口层，只处理请求、响应和参数校验。
- `services`：业务逻辑层，例如记账、预算、AI 解析、分类推断。
- `repositories`：数据访问层，后续可以从 SQLite 替换成 PostgreSQL。
- `domain`：领域模型、枚举、数据结构。
- `core`：配置、数据库连接、应用启动逻辑。

## AI 模块边界

AI 能力通过 `AiParser` 抽象暴露。第一阶段可以用规则和关键词模拟，第二阶段接入真实大模型，第三阶段加入用户纠错后的个性化分类学习。

## 桌面端模块

- `main`：Electron 主进程，管理窗口、系统托盘、文件权限等。
- `preload`：安全暴露桌面能力给渲染层。
- `renderer`：React 应用，包含聊天记账、账单、统计、预算、设置页面。

## 后续可扩展方向

- 数据库迁移：引入 Alembic。
- 用户系统：本地用户、多账本、家庭共享。
- AI 供应商：OpenAI、本地模型、学校服务器模型都通过同一接口接入。
- 图片识别：新增 `vision_service`，不要把 OCR 逻辑写进路由。
- 统计报表：新增 `analytics_service`，输出统一图表数据结构。
