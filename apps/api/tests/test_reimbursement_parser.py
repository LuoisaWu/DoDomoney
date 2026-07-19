import unittest

from app.domain.schemas import ParsedReimbursement
from app.services.reimbursement_parser import ReimbursementParser, is_reimbursement_message


class FakeClient:
    def __init__(self, result):
        self.result = result

    def complete_json(self, **_kwargs):
        return self.result


class FailingClient:
    def complete_json(self, **_kwargs):
        from app.services.llm_client import LlmError
        raise LlmError("model unavailable")


class ReimbursementParserTests(unittest.TestCase):
    def test_detects_invoice_and_reimbursement_messages(self):
        self.assertTrue(is_reimbursement_message("昨天打车发票 68 元需要报销"))
        self.assertTrue(is_reimbursement_message("帮我记一笔差旅报销"))
        self.assertFalse(is_reimbursement_message("今天午饭 28 元"))

    def test_complete_result_enters_confirmation(self):
        parser = ReimbursementParser(FakeClient({
            "merchant": "滴滴出行", "amount": 68, "invoice_date": "2026-07-13", "category": "交通",
            "invoice_number": "123456", "status": "pending", "note": "出差打车", "confidence": 0.95,
            "follow_up_fields": [], "follow_up_question": None,
        }))
        result = parser.parse("昨天滴滴发票 68 元")
        self.assertTrue(result.is_complete)
        self.assertEqual(result.merchant, "滴滴出行")

    def test_missing_field_uses_local_follow_up(self):
        parser = ReimbursementParser(FakeClient({
            "merchant": "某酒店", "amount": 500, "invoice_date": "2026-07-13", "category": None,
            "confidence": 0.8, "follow_up_fields": [], "follow_up_question": None,
        }))
        result = parser.parse("酒店发票 500 元")
        self.assertEqual(result.follow_up_fields, ["category"])
        self.assertIn("类别", result.follow_up_question)

    def test_falls_back_to_local_parser_when_llm_fails(self):
        parser = ReimbursementParser(FailingClient())
        result = parser.parse("昨天滴滴发票 68 元需要报销")
        self.assertEqual(str(result.amount), "68")
        self.assertEqual(result.category, "交通")
        self.assertEqual(result.merchant, "滴滴")
        self.assertTrue(result.invoice_date)

    def test_local_fallback_merges_plain_follow_up_answer(self):
        parser = ReimbursementParser(FailingClient())
        pending = ParsedReimbursement(
            merchant="滴滴", invoice_date="2026-07-13", category="交通",
            follow_up_fields=["amount"], follow_up_question="金额是多少？",
        )
        result = parser.parse("68", pending)
        self.assertEqual(str(result.amount), "68")
        self.assertTrue(result.is_complete)

    def test_local_fallback_maps_ocr_seller_and_invoice_title(self):
        parser = ReimbursementParser(FailingClient())
        result = parser.parse(
            "图片 OCR 文字：销售方/开具单位：深圳市某某科技有限公司\n"
            "购买方/发票抬头：上海某某信息技术有限公司\n"
            "价税合计/总金额：11.21\n开票日期：2026-07-15\n费用类别：交通"
        )
        self.assertEqual(result.merchant, "深圳市某某科技有限公司")
        self.assertEqual(result.invoice_title, "上海某某信息技术有限公司")
        self.assertEqual(str(result.amount), "11.21")


if __name__ == "__main__":
    unittest.main()
