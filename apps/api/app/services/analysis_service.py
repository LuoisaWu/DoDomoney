import json
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from pydantic import ValidationError

from app.domain.schemas import AnalysisInsight, CategorySummary, DailyCashFlow, PeriodAnalysis, SpecialFlowSummary
from app.repositories.entry_repository import EntryRepository
from app.services.llm_client import LlmClient, LlmError


ZERO = Decimal("0")


class AnalysisService:
    """Build range-based financial analysis and optionally explain aggregates with an LLM."""

    BORROWED_WORDS = ("借入", "借款", "借到", "贷款到账", "收到借款")
    REPAYMENT_RECEIVED_WORDS = ("收到还款", "收回借款", "还我", "还钱给我", "归还借款")
    LENT_OUT_WORDS = ("借出", "借给", "出借")
    REPAYMENT_PAID_WORDS = ("偿还", "还款", "还贷", "归还贷款", "还钱")

    def __init__(self, repository: EntryRepository | None = None, client: LlmClient | None = None) -> None:
        self.repository = repository or EntryRepository()
        self.client = client or LlmClient()

    def analyze(self, ledger_id: int, start_date: date, end_date: date, include_ai: bool = False) -> PeriodAnalysis:
        entries = self.repository.list_entries_in_range(ledger_id, start_date, end_date)
        days = (end_date - start_date).days + 1
        expense_total = ZERO
        income_total = ZERO
        consumption_total = ZERO
        ordinary_income_total = ZERO
        special = {key: {"amount": ZERO, "count": 0} for key in ("borrowed", "repayment_received", "lent_out", "repayment_paid")}
        categories: dict[str, Decimal] = defaultdict(lambda: ZERO)
        daily: dict[date, dict[str, Decimal]] = defaultdict(lambda: {"expense": ZERO, "income": ZERO})

        for entry in entries:
            amount = entry.amount
            day = entry.occurred_at.date()
            daily[day][entry.type.value] += amount
            if entry.type.value == "expense":
                expense_total += amount
            else:
                income_total += amount

            flow_type = self._special_flow(entry.type.value, entry.category, entry.description)
            if flow_type:
                special[flow_type]["amount"] += amount
                special[flow_type]["count"] += 1
            elif entry.type.value == "expense":
                consumption_total += amount
                categories[entry.category] += amount
            else:
                ordinary_income_total += amount

        category_rows = [
            CategorySummary(
                category=name,
                amount=amount,
                percentage=round(float(amount / consumption_total * 100), 1) if consumption_total else 0,
            )
            for name, amount in sorted(categories.items(), key=lambda item: item[1], reverse=True)
        ]
        daily_rows = []
        cursor = start_date
        while cursor <= end_date:
            totals = daily[cursor]
            daily_rows.append(DailyCashFlow(date=cursor, expense=totals["expense"], income=totals["income"]))
            cursor += timedelta(days=1)

        insight = self._local_insight(days, consumption_total, ordinary_income_total, expense_total, income_total, category_rows, special)
        ai_used = False
        ai_warning = None
        if include_ai and entries:
            try:
                insight = self._ai_insight(start_date, end_date, len(entries), consumption_total, ordinary_income_total, expense_total, income_total, category_rows, special)
                ai_used = True
            except (LlmError, ValidationError) as exc:
                ai_warning = f"AI 解读暂不可用，已展示本地分析：{exc}"

        return PeriodAnalysis(
            start_date=start_date,
            end_date=end_date,
            days=days,
            entry_count=len(entries),
            expense_total=expense_total,
            income_total=income_total,
            balance=income_total - expense_total,
            consumption_total=consumption_total,
            ordinary_income_total=ordinary_income_total,
            average_daily_consumption=(consumption_total / days).quantize(Decimal("0.01")),
            borrowed=SpecialFlowSummary(**special["borrowed"]),
            repayment_received=SpecialFlowSummary(**special["repayment_received"]),
            lent_out=SpecialFlowSummary(**special["lent_out"]),
            repayment_paid=SpecialFlowSummary(**special["repayment_paid"]),
            categories=category_rows,
            daily=daily_rows,
            insight=insight,
            ai_used=ai_used,
            ai_warning=ai_warning,
        )

    def _special_flow(self, entry_type: str, category: str, description: str) -> str | None:
        text = f"{category} {description}".lower()
        if entry_type == "income":
            received_repayment = (
                any(word in text for word in self.REPAYMENT_RECEIVED_WORDS)
                or (any(word in text for word in ("还款", "还钱", "归还")) and any(word in text for word in ("收到", "收回", "还我", "回款")))
            )
            if received_repayment:
                return "repayment_received"
            if any(word in text for word in self.BORROWED_WORDS):
                return "borrowed"
        else:
            if any(word in text for word in self.LENT_OUT_WORDS):
                return "lent_out"
            if any(word in text for word in self.REPAYMENT_PAID_WORDS):
                return "repayment_paid"
        return None

    @staticmethod
    def _local_insight(days: int, consumption: Decimal, ordinary_income: Decimal, expense: Decimal, income: Decimal, categories: list[CategorySummary], special: dict) -> AnalysisInsight:
        if not expense and not income:
            return AnalysisInsight(headline="这段时间还没有账单", summary="选择其他日期，或先记录几笔收支后再来分析。", highlights=[], suggestions=["坚持记录每笔收支，分析会越来越准确。"])
        top = categories[0] if categories else None
        highlights = [f"日均消费 ¥{consumption / days:.2f}"]
        if top:
            highlights.append(f"{top.category}是最大消费项，占消费的 {top.percentage}%")
        if special["borrowed"]["amount"]:
            highlights.append(f"期间新增借入 ¥{special['borrowed']['amount']:.2f}")
        if special["repayment_received"]["amount"]:
            highlights.append(f"期间收到他人还款 ¥{special['repayment_received']['amount']:.2f}")
        suggestions = []
        if consumption > ordinary_income and ordinary_income:
            suggestions.append("消费高于普通收入，建议复查最大消费分类并设置预算。")
        elif top and top.percentage >= 40:
            suggestions.append(f"{top.category}占比较高，可以从这个分类开始优化。")
        else:
            suggestions.append("当前收支结构较平稳，继续保持分类记账。")
        return AnalysisInsight(
            headline="本期有结余" if income >= expense else "本期现金净流出",
            summary=f"共分析 {days} 天，消费 ¥{consumption:.2f}、普通收入 ¥{ordinary_income:.2f}，全部现金流结余 ¥{income - expense:.2f}。",
            highlights=highlights[:5],
            suggestions=suggestions,
        )

    def _ai_insight(self, start_date: date, end_date: date, entry_count: int, consumption: Decimal, ordinary_income: Decimal, expense: Decimal, income: Decimal, categories: list[CategorySummary], special: dict) -> AnalysisInsight:
        # Only aggregate figures are sent: merchant names and individual descriptions stay local.
        payload = {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "entry_count": entry_count,
            "consumption": str(consumption),
            "ordinary_income": str(ordinary_income),
            "all_expense": str(expense),
            "all_income": str(income),
            "balance": str(income - expense),
            "categories": [item.model_dump(mode="json") for item in categories[:8]],
            "special_flows": {key: {"amount": str(value["amount"]), "count": value["count"]} for key, value in special.items()},
        }
        result = self.client.complete_json(
            system_prompt=(
                "你是谨慎、实用的个人财务分析助手。根据匿名汇总数据用中文给出客观分析，不提供投资建议，不杜撰原因。"
                "只返回 JSON：headline 字符串、summary 字符串、highlights 字符串数组（最多5项）、suggestions 字符串数组（最多5项）。"
                "必须区分普通收入、借入款、收到他人还款；借入和还款不是赚到的钱。"
            ),
            user_prompt=json.dumps(payload, ensure_ascii=False),
        )
        return AnalysisInsight.model_validate(result)
