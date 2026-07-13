# Dodomoney API

FastAPI 后端服务，负责账单、预算、AI 解析和统计分析。

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

接口文档启动后可访问 `http://127.0.0.1:8000/docs`。当前接口包括聊天记账、账单 CRUD、月度统计、分类偏好和预算管理。

首次使用 LLM 记账前，将 `.env.example` 复制为 `.env` 并配置模型密钥。`LLM_BASE_URL` 支持 OpenAI Chat Completions 兼容服务。

## API 入口

- `GET /health`：健康检查。
- `POST /chat/record`：自然语言记账。
- `GET /users/me/persona`：读取当前用户的助手人格。
- `PUT /users/me/persona`：保存当前用户的助手人格。
- `GET /entries`：账单列表。
- `POST /entries`：创建账单。
- `PATCH /entries/{entry_id}`：更新账单。
- `DELETE /entries/{entry_id}`：删除账单。
- `GET /budgets`：预算列表。
- `POST /budgets`：创建预算。
