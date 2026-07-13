import json
import re
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from app.domain.schemas import ParsedTransaction
from app.services.llm_client import LlmClient, LlmError


class AiParser:
    """Parse natural-language bookkeeping messages exclusively through an LLM."""

    def __init__(self, client: LlmClient | None = None) -> None:
        self.client = client or LlmClient()

    def parse(self, message: str, pending_context: ParsedTransaction | None = None) -> ParsedTransaction:
        # China Standard Time has no daylight-saving transitions. A fixed
        # offset avoids requiring the optional IANA tzdata package on Windows.
        now = datetime.now(timezone(timedelta(hours=8), name="Asia/Shanghai"))
        fast_result = self._fast_parse(message, pending_context, now)
        if fast_result is not None:
            return fast_result
        context = pending_context.model_dump(mode="json") if pending_context else None
        system_prompt = f"""
你是 Dodomoney 的记账语义解析器。当前时间是 {now.isoformat()}，时区 Asia/Shanghai。
只返回一个 JSON 对象，不要解释。必须包含这些键：
amount（正数或 null）、category（字符串或 null）、occurred_at（ISO 8601 时间或 null）、
type（expense、income 或 null）、confidence（0 到 1）、follow_up_fields（缺失字段数组）、
follow_up_question（需要补充时的一句中文问题，否则 null）、description（简短备注或 null）、subcategory（字符串或 null）。
允许的 follow_up_fields 只有 amount、category、occurred_at、type。
常见分类：餐饮、交通出行、购物、娱乐、学习办公、健康、其他支出、工资、兼职、其他收入。
规则：
1. 从语义理解金额、收支、分类和相对时间，不能使用臆测的金额。
2. 用户没有说时间时，可将 occurred_at 设为当前时间，不必追问。
3. 分类可以根据消费场景合理推断；无法判断时才追问。
4. 有待补上下文时，把新消息与旧结果合并，保留旧结果中用户未更改的字段。
5. 任一必需字段 amount/category/occurred_at/type 为空时，将字段列入 follow_up_fields，且只追问最关键的信息。
6. description 应保留商户、用途等有价值的信息，不要重复金额。
""".strip()
        user_prompt = json.dumps(
            {"message": message, "pending_context": context},
            ensure_ascii=False,
        )
        try:
            result = ParsedTransaction.model_validate(
                self.client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
            )
        except ValidationError as exc:
            raise LlmError(f"LLM 解析结果字段不合法：{exc.errors()[0]['msg']}") from exc

        missing = [
            field
            for field in ("amount", "category", "occurred_at", "type")
            if getattr(result, field) is None
        ]
        if set(missing) != set(result.follow_up_fields):
            result = result.model_copy(update={"follow_up_fields": missing})
        return result

    @staticmethod
    def _fast_parse(
        message: str,
        pending_context: ParsedTransaction | None,
        now: datetime,
    ) -> ParsedTransaction | None:
        """Handle common one-line bookkeeping locally, avoiding network latency."""
        text = message.strip()
        amount_match = re.search(r"(?:¥|￥)?\s*(\d+(?:\.\d{1,2})?)\s*(?:元|块|块钱|¥|￥)", text, re.I)
        if amount_match is None and pending_context is not None:
            amount_match = re.fullmatch(r"\s*(\d+(?:\.\d{1,2})?)\s*", text)

        income_words = ("工资", "奖金", "报销", "兼职", "收款", "到账", "收入", "赚了", "红包")
        categories = {
            "餐饮": ("早餐", "午饭", "午餐", "晚饭", "晚餐", "吃饭", "外卖", "咖啡", "奶茶", "餐厅"),
            "交通出行": ("打车", "出租车", "地铁", "公交", "高铁", "火车", "机票", "加油", "停车"),
            "购物": ("购物", "衣服", "鞋", "淘宝", "京东", "超市", "日用品"),
            "娱乐": ("电影", "游戏", "唱歌", "演出", "娱乐"),
            "学习办公": ("书", "课程", "培训", "文具", "办公"),
            "健康": ("医院", "看病", "药", "体检", "健身"),
            "工资": ("工资", "奖金"),
            "兼职": ("兼职",),
            "其他收入": ("报销", "收款", "到账", "收入", "赚了", "红包"),
        }
        detected_category = next(
            (category for category, words in categories.items() if any(word in text for word in words)),
            None,
        )
        detected_type = "income" if any(word in text for word in income_words) else ("expense" if detected_category else None)

        base = pending_context.model_dump() if pending_context else {}
        amount = Decimal(amount_match.group(1)) if amount_match else base.get("amount")
        category = detected_category or base.get("category")
        entry_type = detected_type or base.get("type")
        occurred_at = base.get("occurred_at") or now
        if "昨天" in text:
            occurred_at = now - timedelta(days=1)
        elif "前天" in text:
            occurred_at = now - timedelta(days=2)

        # Let the model handle ambiguous messages; the local path is intentionally conservative.
        if amount is None or (category is None and pending_context is None):
            return None
        missing = [
            field for field, value in (
                ("amount", amount), ("category", category), ("occurred_at", occurred_at), ("type", entry_type)
            ) if value is None
        ]
        question = None
        if missing:
            question = {"category": "这笔钱主要花在什么地方？", "type": "这是收入还是支出？"}.get(missing[0])
        return ParsedTransaction(
            amount=amount,
            category=category,
            occurred_at=occurred_at,
            type=entry_type,
            confidence=0.96 if not missing else 0.8,
            follow_up_fields=missing,
            follow_up_question=question,
            description=text if pending_context is None else (base.get("description") or text),
            subcategory=base.get("subcategory"),
        )
