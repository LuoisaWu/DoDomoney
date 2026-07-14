import json
import unittest
from datetime import date
from decimal import Decimal

from app.domain.schemas import ParsedLoan
from app.services.loan_parser import LoanParser, is_cancellation, is_confirmation, is_loan_message


def loan_result(**overrides):
    result = {
        "creditor": None,
        "borrowed_at": None,
        "principal": None,
        "repayment_months": None,
        "annual_rate": None,
        "repayment_method": None,
        "first_payment_date": None,
        "note": "来自 AI 记账输入",
        "confidence": 0.9,
        "follow_up_fields": [],
        "follow_up_question": None,
    }
    result.update(overrides)
    return result


class FakeClient:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def complete_json(self, **kwargs):
        self.calls.append(kwargs)
        return self.results.pop(0)


class LoanParserTests(unittest.TestCase):
    def test_screenshot_sentence_uses_semantic_date_and_creditor_roles(self):
        client = FakeClient(loan_result(
            creditor="张三",
            borrowed_at="2026-07-14",
            principal=300,
            repayment_months=1,
            repayment_method="equal_payment",
            first_payment_date="2026-07-20",
            follow_up_question="这笔借款有利息吗？",
        ))
        result = LoanParser(client).parse("我刚刚借了张三300块钱，说的是7月20号还")

        self.assertEqual(result.creditor, "张三")
        self.assertEqual(result.borrowed_at, date(2026, 7, 14))
        self.assertEqual(result.first_payment_date, date(2026, 7, 20))
        self.assertEqual(result.principal, Decimal("300"))
        self.assertEqual(result.follow_up_fields, ["annual_rate"])
        self.assertIn("7月20号还", client.calls[0]["system_prompt"])
        self.assertIn("只能是“张三”", client.calls[0]["system_prompt"])

    def test_follow_up_passes_structured_context_to_model(self):
        pending = ParsedLoan.model_validate(loan_result(
            creditor="张三",
            borrowed_at="2026-07-14",
            principal=300,
            repayment_months=1,
            repayment_method="equal_payment",
            first_payment_date="2026-07-20",
            follow_up_fields=["annual_rate"],
        ))
        client = FakeClient(loan_result(
            creditor="张三",
            borrowed_at="2026-07-14",
            principal=300,
            repayment_months=1,
            annual_rate=0,
            repayment_method="equal_payment",
            first_payment_date="2026-07-20",
        ))

        result = LoanParser(client).parse("没有利息", pending)
        sent = json.loads(client.calls[0]["user_prompt"])

        self.assertEqual(sent["pending_context"]["creditor"], "张三")
        self.assertEqual(result.annual_rate, Decimal("0"))
        self.assertTrue(result.is_complete)
        self.assertFalse(result.awaiting_confirmation)

    def test_server_recomputes_missing_fields_instead_of_trusting_model_list(self):
        client = FakeClient(loan_result(follow_up_fields=[]))
        result = LoanParser(client).parse("我借钱了")

        self.assertEqual(result.follow_up_fields[0], "principal")
        self.assertIn("本金", result.follow_up_question)

    def test_intent_and_confirmation_controls(self):
        self.assertFalse(is_loan_message("我借给小王500元"))
        self.assertFalse(is_loan_message("今天还贷款2000元"))
        self.assertTrue(is_loan_message("我找张三借了300元"))
        self.assertTrue(is_loan_message("我从银行借款1万元，首次还款日8月20日"))
        self.assertTrue(is_confirmation("确认入库"))
        self.assertTrue(is_confirmation("没问题"))
        self.assertTrue(is_cancellation("不记录了"))
        self.assertFalse(is_confirmation("利率改成3%"))


if __name__ == "__main__":
    unittest.main()
