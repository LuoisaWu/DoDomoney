from datetime import datetime
from decimal import Decimal
import re

from app.domain.enums import EntryType
from app.domain.schemas import ParsedEntry
from app.services.category_service import CategoryService


class AiParser:
    """Starter parser. Replace internals with an LLM provider later."""

    amount_pattern = re.compile(r"(?P<amount>\d+(?:\.\d{1,2})?)\s*(元|块|rmb|￥)?", re.IGNORECASE)

    def __init__(self, category_service: CategoryService | None = None) -> None:
        self.category_service = category_service or CategoryService()

    def parse(self, message: str) -> ParsedEntry:
        amount = self._extract_amount(message)
        entry_type = self._infer_type(message)
        category, subcategory = self.category_service.infer_category(message, entry_type)

        return ParsedEntry(
            type=entry_type,
            amount=amount,
            category=category,
            subcategory=subcategory,
            description=self._clean_description(message),
            occurred_at=datetime.now(),
            confidence=0.72,
        )

    def _extract_amount(self, message: str) -> Decimal:
        match = self.amount_pattern.search(message)
        if match is None:
            raise ValueError("未识别到金额，请补充金额，例如：午饭 22 元。")
        return Decimal(match.group("amount"))

    def _infer_type(self, message: str) -> EntryType:
        income_keywords = ["收入", "工资", "奖金", "报销到账", "收到", "赚了"]
        if any(keyword in message for keyword in income_keywords):
            return EntryType.INCOME
        return EntryType.EXPENSE

    def _clean_description(self, message: str) -> str:
        return self.amount_pattern.sub("", message).strip(" ，,。.")
