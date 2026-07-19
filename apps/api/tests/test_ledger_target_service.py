import unittest
from types import SimpleNamespace

from app.services.ledger_target_service import extract_ledger_directive, find_accessible_ledger


class LedgerTargetServiceTests(unittest.TestCase):
    def setUp(self):
        self.ledgers = [
            SimpleNamespace(id=1, name="个人账本"),
            SimpleNamespace(id=2, name="旅行基金"),
            SimpleNamespace(id=3, name="家庭账本"),
        ]

    def test_extracts_suffix_directive_without_polluting_transaction(self):
        result = extract_ledger_directive("今天午饭花了30元，记到旅行基金账本")
        self.assertIsNotNone(result)
        self.assertEqual(result.ledger_name, "旅行基金")
        self.assertEqual(result.remaining_message, "今天午饭花了30元")

    def test_extracts_prefix_directive(self):
        result = extract_ledger_directive("在家庭账本里记录昨天买菜80元")
        self.assertIsNotNone(result)
        self.assertEqual(result.ledger_name, "家庭")
        self.assertEqual(result.remaining_message, "昨天买菜80元")

    def test_extracts_record_to_directive(self):
        result = extract_ledger_directive("打车42元，记录到旅行基金账本")
        self.assertIsNotNone(result)
        self.assertEqual(result.ledger_name, "旅行基金")
        self.assertEqual(result.remaining_message, "打车42元")

    def test_finds_only_accessible_exact_ledger(self):
        self.assertEqual(find_accessible_ledger("旅行基金", self.ledgers).id, 2)
        self.assertEqual(find_accessible_ledger("我的旅行基金", self.ledgers).id, 2)
        self.assertIsNone(find_accessible_ledger("公司秘密", self.ledgers))


if __name__ == "__main__":
    unittest.main()
