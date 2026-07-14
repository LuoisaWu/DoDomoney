import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


class LlmError(RuntimeError):
    """Raised when the configured language model cannot return a usable response."""


class LlmClient:
    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        if not settings.llm_api_key and "localhost" not in settings.llm_base_url and "127.0.0.1" not in settings.llm_base_url:
            raise LlmError("尚未配置 LLM。请设置 DODOMONEY_LLM_API_KEY 后重启后端。")

        payload = {
            "model": settings.llm_model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Content-Type": "application/json"}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"
        request = Request(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=settings.llm_timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            return self._decode_json(content)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise LlmError(f"LLM 请求失败（HTTP {exc.code}）：{detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise LlmError(f"无法连接 LLM 服务：{exc}") from exc
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LlmError("LLM 返回了无法识别的结构化结果。") from exc

    @staticmethod
    def _decode_json(content: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(content, dict):
            return content
        text = content.strip()
        if text.startswith("```"):
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(text)
        if not isinstance(result, dict):
            raise json.JSONDecodeError("Expected JSON object", text, 0)
        return result
