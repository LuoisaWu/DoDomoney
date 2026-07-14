import json
import re
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from app.domain.schemas import LoanFollowUpField, ParsedLoan
from app.services.llm_client import LlmClient, LlmError


FIELD_ORDER: tuple[LoanFollowUpField, ...] = (
    "principal",
    "creditor",
    "borrowed_at",
    "repayment_months",
    "annual_rate",
    "repayment_method",
    "first_payment_date",
)

QUESTIONS: dict[LoanFollowUpField, str] = {
    "principal": "这笔借款的本金是多少元？",
    "creditor": "这笔钱是从谁或哪个平台借的？",
    "borrowed_at": "实际借到这笔钱是哪一天？",
    "repayment_months": "这笔借款准备分几次还清？",
    "annual_rate": "这笔借款有利息吗？有的话请告诉我年利率，没有请回复“免息”。",
    "repayment_method": "如果分期，还款方式是等额本息还是等额本金？",
    "first_payment_date": "第一次还款是哪一天？",
}


def is_loan_message(message: str) -> bool:
    text = message.strip()
    if re.search(r"借给|借出", text):
        return False
    acquisition = bool(re.search(r"借了|借到|借入|从.+借|找.+借|向.+借|贷款到账", text))
    repayment = bool(re.search(r"还款|还贷|归还", text))
    generic_loan = bool(re.search(r"借款|贷款", text)) and not repayment
    return acquisition or generic_loan


def is_confirmation(message: str) -> bool:
    return bool(re.fullmatch(r"\s*(确认(?:入库|记录)?|确认无误|没问题|正确|对的|是的|保存|入库|记录吧|可以)\s*[。！!]?\s*", message))


def is_cancellation(message: str) -> bool:
    return bool(re.fullmatch(r"\s*(取消|不记录了|不要了|算了)\s*[。！!]?\s*", message))


class LoanParser:
    """Use the configured language model to understand and merge loan semantics."""

    def __init__(self, client: LlmClient | None = None) -> None:
        self.client = client or LlmClient()

    def parse(self, message: str, pending: ParsedLoan | None = None) -> ParsedLoan:
        now = datetime.now(timezone(timedelta(hours=8), name="Asia/Shanghai"))
        context = pending.model_dump(mode="json", exclude={"awaiting_confirmation"}) if pending else None
        system_prompt = f"""
你是 Dodomoney 的借款语义解析器。当前时间是 {now.isoformat()}，时区 Asia/Shanghai。
理解用户整句话的含义以及指代关系，只返回一个 JSON 对象，不要解释。必须包含：
creditor（出借人或放款平台的干净名称）、borrowed_at（实际收到借款的 YYYY-MM-DD）、
principal（正数本金）、repayment_months（还款次数/期数）、annual_rate（百分数值，免息为 0）、
repayment_method（equal_payment、equal_principal 或 null）、first_payment_date（首次/约定还款日 YYYY-MM-DD）、
note（保留最初借款描述）、confidence（0 到 1）、follow_up_fields（缺失字段数组）、
follow_up_question（只追问当前最关键缺失信息的一句自然中文，否则 null）。

语义规则：
1. “刚刚、刚才、今天借了”表示 borrowed_at 是今天；“7月20号还、到7月20号还”表示 first_payment_date，绝不能当成 borrowed_at。
2. “找张三借的啊”“从张三那里借的”中的 creditor 只能是“张三”，不要复制“找、借的、啊”等口语外壳。
3. 金额单位要换算：“300块”是 300，“1万”是 10000。
4. 新消息是对追问的回答或对已有信息的修改时，与 pending_context 合并；保留没有被修改的旧字段。
5. 不得臆测利率。用户明确“免息、没利息”时 annual_rate 才是 0。
6. 用户明确只在某一天一次还清时，可令 repayment_months=1、repayment_method=equal_payment；这是内部的一次性还款表示。
7. 普通分期但未说明等额本息/等额本金时，不得猜测 repayment_method。
8. 日期必须根据句子中的“借、收到、到账、还、归还、首期”等谓词正确归属。
9. 必填字段为 creditor、borrowed_at、principal、repayment_months、annual_rate、repayment_method、first_payment_date。
10. follow_up_fields 只允许上述七个字段；信息不完整时只生成一个 follow_up_question。
""".strip()
        user_prompt = json.dumps(
            {"message": message, "pending_context": context},
            ensure_ascii=False,
        )
        try:
            result = ParsedLoan.model_validate(
                self.client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
            )
        except ValidationError as exc:
            raise LlmError(f"LLM 借款解析结果字段不合法：{exc.errors()[0]['msg']}") from exc

        missing = [field for field in FIELD_ORDER if getattr(result, field) is None]
        question = result.follow_up_question
        if missing and not question:
            question = QUESTIONS[missing[0]]
        return result.model_copy(
            update={
                "follow_up_fields": missing,
                "follow_up_question": question if missing else None,
                "awaiting_confirmation": False,
            }
        )
