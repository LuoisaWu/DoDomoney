import json
import re
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from app.domain.schemas import ParsedReimbursement, ReimbursementFollowUpField
from app.services.llm_client import LlmClient, LlmError

FIELD_ORDER: tuple[ReimbursementFollowUpField, ...] = ("amount", "merchant", "invoice_date", "category")
QUESTIONS = {
    "amount": "这张发票要报销多少钱？",
    "merchant": "发票是哪家商户或单位开具的？",
    "invoice_date": "发票日期是哪一天？",
    "category": "这笔报销属于什么类别，例如交通、餐饮、住宿或办公？",
}


def is_reimbursement_message(message: str) -> bool:
    return bool(re.search(r"发票|报销|费用单|差旅单", message.strip()))


class ReimbursementParser:
    def __init__(self, client: LlmClient | None = None) -> None:
        self.client = client or LlmClient()

    def parse(self, message: str, pending: ParsedReimbursement | None = None) -> ParsedReimbursement:
        now = datetime.now(timezone(timedelta(hours=8), name="Asia/Shanghai"))
        context = pending.model_dump(mode="json", exclude={"awaiting_confirmation"}) if pending else None
        system_prompt = f"""
你是 Dodomoney 的发票报销语义解析器。当前时间是 {now.isoformat()}，时区 Asia/Shanghai。
只返回 JSON 对象，必须包含 merchant、invoice_title、amount、invoice_date（YYYY-MM-DD）、category、invoice_number、
status（pending/submitted/reimbursed）、note、confidence、follow_up_fields、follow_up_question。
必填字段为 merchant、amount、invoice_date、category。用户未说明状态时使用 pending。
新消息是追问回答或修改时与 pending_context 合并，不得丢掉已有字段；金额单位要正确换算。
图片 OCR 中“销售方/开具单位”映射到 merchant，“购买方/发票抬头”映射到 invoice_title。
category 使用简洁中文类别，例如交通、餐饮、住宿、办公、通讯、其他。不得臆测发票号。
follow_up_fields 只能包含 merchant、amount、invoice_date、category，并且一次只追问最关键的一项。
""".strip()
        try:
            result = ParsedReimbursement.model_validate(self.client.complete_json(
                system_prompt=system_prompt,
                user_prompt=json.dumps({"message": message, "pending_context": context}, ensure_ascii=False),
            ))
        except LlmError:
            result = self._parse_locally(message, pending, now)
        except ValidationError as exc:
            result = self._parse_locally(message, pending, now)
        missing = [field for field in FIELD_ORDER if getattr(result, field) is None]
        question = result.follow_up_question or (QUESTIONS[missing[0]] if missing else None)
        return result.model_copy(update={
            "follow_up_fields": missing,
            "follow_up_question": question if missing else None,
            "awaiting_confirmation": False,
        })

    @staticmethod
    def _parse_locally(
        message: str,
        pending: ParsedReimbursement | None,
        now: datetime,
    ) -> ParsedReimbursement:
        """Keep reimbursement recording usable when the configured LLM is unavailable."""
        text = message.strip()
        base = pending.model_dump() if pending else {}

        amount_match = re.search(
            r"(?:价税合计/总金额|价税合计（小写）|总金额)[：:\s¥￥]*(\d+(?:\.\d{1,2})?)",
            text,
            re.I,
        )
        if not amount_match:
            amount_match = re.search(r"(?<!\d)(\d+(?:\.\d{1,2})?)\s*(?:元|块|块钱|rmb|人民币)", text, re.I)
        if not amount_match and pending and "amount" in pending.follow_up_fields:
            amount_match = re.fullmatch(r"\s*(\d+(?:\.\d{1,2})?)\s*", text)
        if amount_match:
            base["amount"] = amount_match.group(1)

        date_value = None
        if re.search(r"今天|今日", text):
            date_value = now.date()
        elif re.search(r"昨天|昨日", text):
            date_value = (now - timedelta(days=1)).date()
        elif re.search(r"前天", text):
            date_value = (now - timedelta(days=2)).date()
        else:
            date_match = re.search(r"(?:(\d{4})[年./-])?(\d{1,2})[月./-](\d{1,2})日?", text)
            if date_match:
                year = int(date_match.group(1) or now.year)
                try:
                    date_value = datetime(year, int(date_match.group(2)), int(date_match.group(3))).date()
                except ValueError:
                    date_value = None
        if date_value:
            base["invoice_date"] = date_value

        category_rules = (
            ("交通", r"打车|滴滴|出租|地铁|公交|高铁|火车|机票|交通|过路费|停车"),
            ("餐饮", r"餐饮|吃饭|午饭|晚饭|早餐|餐费|饭店|餐厅"),
            ("住宿", r"住宿|酒店|宾馆|旅店"),
            ("办公", r"办公|文具|打印|耗材|设备"),
            ("通讯", r"话费|通讯|宽带|流量"),
        )
        for category, pattern in category_rules:
            if re.search(pattern, text):
                base["category"] = category
                break
        if pending and "category" in pending.follow_up_fields and text in {"交通", "餐饮", "住宿", "办公", "通讯", "其他"}:
            base["category"] = text

        invoice_match = re.search(r"(?:发票号|票号|发票号码)[：:\s]*([A-Za-z0-9-]{5,})", text)
        if invoice_match:
            base["invoice_number"] = invoice_match.group(1)
        title_match = re.search(r"(?:购买方/发票抬头|发票抬头|购买方名称)[：:\s]*([^\n，。；,]{2,120})", text)
        if title_match:
            base["invoice_title"] = title_match.group(1).strip()

        merchant_patterns = (
            r"(?:销售方/开具单位|销售方名称|开具单位)[：:\s]*([^\n，。；,]{2,120})",
            r"(?:商户|开票方|单位)[是为：:\s]+([^，。；,\s]{2,30})",
            r"(?:在|从)([^，。；,\s]{2,20})(?:开了?|拿了?|取得)(?:一张)?发票",
            r"([^，。；,\s]{2,20})(?:的)?发票",
        )
        for pattern in merchant_patterns:
            merchant_match = re.search(pattern, text)
            if merchant_match:
                candidate = re.sub(r"^(昨天|今天|前天)", "", merchant_match.group(1)).strip()
                if candidate and candidate not in {"这张", "一张", "报销"}:
                    base["merchant"] = candidate
                    break
        if pending and "merchant" in pending.follow_up_fields and not base.get("merchant"):
            candidate = re.sub(r"[，。；,]", "", text).strip()
            if 1 < len(candidate) <= 120:
                base["merchant"] = candidate

        base.setdefault("invoice_number", "")
        base.setdefault("invoice_title", "")
        base.setdefault("status", "pending")
        base.setdefault("note", text[:500])
        base["confidence"] = min(float(base.get("confidence") or 0.55), 0.75)
        base["follow_up_fields"] = []
        base["follow_up_question"] = None
        base["awaiting_confirmation"] = False
        return ParsedReimbursement.model_validate(base)
