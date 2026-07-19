import json
from base64 import b64encode
from time import sleep
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


class LlmError(RuntimeError):
    """Raised when the configured language model cannot return a usable response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LlmClient:
    @staticmethod
    def is_configured() -> bool:
        return bool(
            settings.llm_api_key
            or "localhost" in settings.llm_base_url
            or "127.0.0.1" in settings.llm_base_url
        )

    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        if not self.is_configured():
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
        return self._decode_json(self._request_content(payload))

    def complete_json_with_image(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_content: bytes,
        image_content_type: str,
        temperature: float = 0,
    ) -> dict[str, Any]:
        if not self.is_configured():
            raise LlmError("尚未配置视觉模型。请设置 DODOMONEY_LLM_API_KEY 后重启后端。")
        image_url = f"data:{image_content_type};base64,{b64encode(image_content).decode('ascii')}"
        payload = {
            "model": settings.vision_model or settings.llm_model,
            "temperature": temperature,
            "thinking": {"type": "disabled"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": image_url, "detail": "high"}},
                    ],
                },
            ],
        }
        content = self._request_content(payload)
        try:
            return self._decode_json(content)
        except (TypeError, json.JSONDecodeError):
            return self.complete_json(
                system_prompt=(
                    "把视觉模型的识别结果整理成一个合法 JSON 对象。"
                    "只保留原文明确出现的信息，不得补充或猜测；只返回 JSON。"
                ),
                user_prompt=content,
                temperature=0,
            )

    def _request_content(self, payload: dict[str, Any]) -> str | dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"
        request = Request(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=settings.llm_timeout_seconds) as response:
                    body = json.loads(response.read().decode("utf-8"))
                content = body["choices"][0]["message"]["content"]
                if isinstance(content, list):
                    content = "\n".join(
                        str(part.get("text") or "")
                        for part in content
                        if isinstance(part, dict) and part.get("type") == "text"
                    )
                return content
            except HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                if exc.code == 429 and attempt < 2:
                    sleep(attempt + 1)
                    continue
                raise LlmError(
                    f"LLM 请求失败（HTTP {exc.code}）：{detail}",
                    status_code=exc.code,
                ) from exc
            except (URLError, TimeoutError) as exc:
                raise LlmError(f"无法连接 LLM 服务：{exc}") from exc
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
                raise LlmError("LLM 返回了无法识别的结构化结果。") from exc
        raise LlmError("LLM 请求重试后仍未成功。")

    @staticmethod
    def _decode_json(content: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(content, dict):
            return content
        text = content.strip()
        if text.startswith("```"):
            first_newline = text.find("\n")
            if first_newline >= 0:
                text = text[first_newline + 1:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise
            result = json.loads(text[start:end + 1])
        if not isinstance(result, dict):
            raise json.JSONDecodeError("Expected JSON object", text, 0)
        return result
