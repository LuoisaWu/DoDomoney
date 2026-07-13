# Dodomoney API

FastAPI 后端服务，负责账单、预算、AI 解析和统计分析。

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

## API 入口

- `GET /health`：健康检查。
- `POST /chat/record`：自然语言记账。
- `GET /entries`：账单列表。
- `POST /entries`：创建账单。
- `PATCH /entries/{entry_id}`：更新账单。
- `DELETE /entries/{entry_id}`：删除账单。
- `GET /budgets`：预算列表。
- `POST /budgets`：创建预算。
