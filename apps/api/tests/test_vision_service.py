import unittest

from app.services.llm_client import LlmClient, LlmError
from app.services.vision_service import VisionService


class FakeVisionClient:
    @staticmethod
    def is_configured():
        return True

    def complete_json_with_image(self, **kwargs):
        self.kwargs = kwargs
        return {
            "document_type": "invoice",
            "seller_name": "深圳市某某科技有限公司",
            "purchaser_name": "上海某某信息技术有限公司",
            "amount": "11.21",
            "invoice_date": "2026-07-15",
            "invoice_number": "51640100MMNT19L5R",
            "category": "交通",
            "raw_text": "价税合计（小写）¥11.21",
            "confidence": 0.96,
        }


class VisionServiceTests(unittest.TestCase):
    def test_extracts_invoice_fields_from_image(self):
        client = FakeVisionClient()
        result = VisionService(client).analyze(b"fake-image", "image/jpeg")

        self.assertEqual(result.document_type, "invoice")
        self.assertEqual(result.status, "completed")
        self.assertIn("销售方/开具单位：深圳市某某科技有限公司", result.extracted_text)
        self.assertIn("购买方/发票抬头：上海某某信息技术有限公司", result.extracted_text)
        self.assertIn("价税合计/总金额：11.21", result.extracted_text)
        self.assertEqual(client.kwargs["image_content"], b"fake-image")

    def test_unconfigured_provider_does_not_claim_ocr_completed(self):
        class UnconfiguredClient:
            @staticmethod
            def is_configured():
                return False

        result = VisionService(UnconfiguredClient()).analyze(b"fake-image", "image/jpeg")
        self.assertEqual(result.status, "pending_provider")
        self.assertEqual(result.extracted_text, "")

    def test_vision_request_avoids_text_only_response_format_and_parses_fence(self):
        class CapturingClient(LlmClient):
            def _request_content(self, payload):
                self.payload = payload
                return '识别结果如下：\n```json\n{"document_type":"invoice","amount":11.55}\n```'

        client = CapturingClient()
        result = client.complete_json_with_image(
            system_prompt="read invoice",
            user_prompt="extract fields",
            image_content=b"fake-image",
            image_content_type="image/jpeg",
        )
        self.assertEqual(result["amount"], 11.55)
        self.assertNotIn("response_format", client.payload)
        self.assertEqual(client.payload["thinking"], {"type": "disabled"})

    def test_busy_provider_returns_specific_retry_message(self):
        class BusyClient:
            @staticmethod
            def is_configured():
                return True

            @staticmethod
            def complete_json_with_image(**_kwargs):
                raise LlmError("HTTP 429", status_code=429)

        with self.assertRaisesRegex(LlmError, "请求量过高"):
            VisionService(BusyClient()).analyze(b"fake-image", "image/jpeg")


if __name__ == "__main__":
    unittest.main()
