from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from app.core.config import settings
from app.services.llm_client import LlmClient, LlmError


@dataclass(frozen=True)
class VisionResult:
    extracted_text: str = ""
    document_type: str = "unknown"
    confidence: float = 0
    status: str = "pending_provider"


class VisionService:
    """Extract document fields with the configured OpenAI-compatible vision model."""

    def __init__(self, client: LlmClient | None = None) -> None:
        self.client = client or LlmClient()

    @property
    def provider_configured(self) -> bool:
        return self.client.is_configured()

    def analyze(self, content: bytes, content_type: str) -> VisionResult:
        if not self.provider_configured:
            return VisionResult()
        system_prompt = """
你是财务单据视觉识别器。必须直接阅读图片，而不是根据用户描述猜测。
只返回 JSON 对象，包含：
- document_type: invoice、loan_note、repayment、unknown 之一
- seller_name: 销售方名称/开具单位，未看清则为空字符串
- purchaser_name: 购买方名称/发票抬头，未看清则为空字符串
- amount: 价税合计（小写）或实际支付总额，只返回数字；未看清则为 null
- invoice_date: 开票日期，YYYY-MM-DD；未看清则为空字符串
- invoice_number: 发票号码；未看清则为空字符串
- category: 根据票面项目判断的简洁中文费用类别；无法判断则为空字符串
- raw_text: 图片中能可靠辨认的关键原文，保留字段标签
- confidence: 0 到 1
销售方与购买方不得混淆。金额优先取“价税合计（小写）”，不得把税额、单价或用户输入当作总金额。
任何看不清的字段都留空，禁止臆测。
""".strip()
        try:
            data = self.client.complete_json_with_image(
                system_prompt=system_prompt,
                user_prompt="请识别这张单据的类型和关键财务字段。",
                image_content=content,
                image_content_type=content_type,
            )
        except LlmError as exc:
            model = settings.vision_model or settings.llm_model
            if exc.status_code == 429:
                raise LlmError(
                    f"视觉模型 {model} 当前请求量过高，请稍后重试。"
                    "你选择的图片和输入文字会保留。",
                    status_code=429,
                ) from exc
            raise LlmError(
                f"图片识别失败。当前视觉模型为 {model}，请确认它支持图片输入，"
                f"或设置 DODOMONEY_VISION_MODEL 更换视觉模型。原始错误：{exc}"
            ) from exc
        document_type = str(data.get("document_type") or "unknown")
        if document_type not in {"invoice", "loan_note", "repayment", "unknown"}:
            document_type = "unknown"
        confidence = self._confidence(data.get("confidence"))
        extracted_text = self._normalized_text(data)
        return VisionResult(
            extracted_text=extracted_text,
            document_type=document_type,
            confidence=confidence,
            status="completed",
        )

    @staticmethod
    def _confidence(value: Any) -> float:
        try:
            return min(max(float(value), 0), 1)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _normalized_text(data: dict[str, Any]) -> str:
        labels = (
            ("seller_name", "销售方/开具单位"),
            ("purchaser_name", "购买方/发票抬头"),
            ("amount", "价税合计/总金额"),
            ("invoice_date", "开票日期"),
            ("invoice_number", "发票号码"),
            ("category", "费用类别"),
        )
        lines = []
        for key, label in labels:
            value = data.get(key)
            if value is None or str(value).strip() == "":
                continue
            if key == "amount":
                try:
                    value = format(Decimal(str(value).replace("¥", "").replace("￥", "").strip()), "f")
                except InvalidOperation:
                    continue
            lines.append(f"{label}：{str(value).strip()}")
        raw_text = str(data.get("raw_text") or "").strip()
        if raw_text:
            lines.append(f"票面关键原文：{raw_text}")
        return "\n".join(lines)[:10000]
