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

首次使用 LLM 记账前，将 `.env.example` 复制为 `.env` 并配置模型密钥。`DODOMONEY_LLM_BASE_URL` 支持 OpenAI Chat Completions 兼容服务。单据图片默认使用 `DODOMONEY_LLM_MODEL`；如果文本模型不支持图片输入，可通过 `DODOMONEY_VISION_MODEL` 单独指定视觉模型。

## 注册邮箱验证码

注册接口依赖 Redis 保存一次性验证码、60 秒发送冷却、失败尝试次数和请求频率限制。启动 API 前请先启动 Redis，并在 `.env` 中配置 `DODOMONEY_REDIS_URL`、SMTP 参数和一个足够长的随机 `DODOMONEY_VERIFICATION_CODE_SECRET`。使用 465 端口时设置 `DODOMONEY_SMTP_USE_SSL=true`、`DODOMONEY_SMTP_USE_TLS=false`；使用 587 STARTTLS 时设置相反。开发联调时可以临时启用 `DODOMONEY_EXPOSE_VERIFICATION_CODE=true`；生产环境会拒绝启动此选项。

## API 入口

- `GET /health`：健康检查。
- `POST /chat/record`：自然语言记账。
- `GET/POST/PATCH/DELETE /reimbursements`：发票报销记录管理。
- `POST /uploads/document-ocr`：上传发票、借条或还款记录图片；视觉模型会直接读取图片并提取开具单位、发票抬头、总金额、日期、票号和类别。
- `GET /users/me/persona`：读取当前用户的助手人格。
- `PUT /users/me/persona`：保存当前用户的助手人格。
- `GET /entries`：账单列表。
- `POST /entries`：创建账单。
- `PATCH /entries/{entry_id}`：更新账单。
- `DELETE /entries/{entry_id}`：删除账单。
- `GET /budgets`：预算列表。
- `POST /budgets`：创建预算。
