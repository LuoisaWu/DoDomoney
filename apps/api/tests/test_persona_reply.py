import sqlite3
import unittest
from datetime import datetime, timezone
from decimal import Decimal

from app.core.database import _upgrade_persona_schema
from app.domain.enums import EntryType, PersonaMode, VoiceStyle
from app.domain.schemas import AssistantPersonaRead, ParsedTransaction
from app.services.ai_parser import AiParser
from app.services.assistant_reply_service import AssistantReplyService
from app.services.llm_client import LlmError


class FakeClient:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls = []

    def complete_json(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.result


def persona(mode: PersonaMode = PersonaMode.WITTY_DARK) -> AssistantPersonaRead:
    now = datetime.now(timezone.utc)
    return AssistantPersonaRead(
        user_id=1,
        assistant_name="账小喵",
        avatar="🐱",
        voice_style=VoiceStyle.PLAYFUL,
        mode=mode,
        reply_length="short",
        emoji_level=2,
        proactive_insights=True,
        custom_instructions="称呼我为老板",
        created_at=now,
        updated_at=now,
    )


def parsed_transaction() -> ParsedTransaction:
    return ParsedTransaction(
        amount=Decimal("500"),
        category="餐饮",
        occurred_at=datetime.now(timezone.utc),
        type=EntryType.EXPENSE,
        confidence=0.95,
        description="吃晚饭500元",
    )


class AssistantReplyServiceTests(unittest.TestCase):
    def test_witty_dark_reply_is_generated_by_model_with_avoidance_context(self):
        client = FakeClient({"reply": "老板，晚饭很丰盛，钱包已经开始轻断食了。🐾"})
        service = AssistantReplyService(client)

        reply = service.build_reply(
            parsed_transaction(),
            persona(),
            original_message="吃晚饭500元",
            recent_replies=["旧回复"],
        )

        self.assertEqual(reply, "老板，晚饭很丰盛，钱包已经开始轻断食了。🐾")
        self.assertEqual(client.calls[0]["temperature"], 0.85)
        self.assertIn("幽默腹黑", client.calls[0]["system_prompt"])
        self.assertIn("近期回复", client.calls[0]["user_prompt"])
        self.assertIn("吃晚饭500元", client.calls[0]["user_prompt"])

    def test_reply_failure_uses_transaction_aware_fallback(self):
        client = FakeClient(error=LlmError("offline"))
        reply = AssistantReplyService(client).build_reply(parsed_transaction(), persona())
        self.assertIn("500", reply)
        self.assertIn("餐饮", reply)


class AiParserTests(unittest.TestCase):
    def test_common_message_still_calls_model(self):
        client = FakeClient(parsed_transaction().model_dump(mode="json"))
        result = AiParser(client).parse("吃晚饭500元")
        self.assertEqual(result.amount, Decimal("500"))
        self.assertEqual(len(client.calls), 1)


class PersonaMigrationTests(unittest.TestCase):
    def test_high_legacy_snark_becomes_witty_dark(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript(
            """
            CREATE TABLE users (id INTEGER PRIMARY KEY);
            INSERT INTO users VALUES (1);
            CREATE TABLE assistant_personas (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                assistant_name TEXT NOT NULL,
                avatar TEXT NOT NULL,
                voice_style TEXT NOT NULL,
                snark_level INTEGER NOT NULL,
                mode TEXT NOT NULL,
                reply_length TEXT NOT NULL,
                emoji_level INTEGER NOT NULL,
                proactive_insights INTEGER NOT NULL,
                custom_instructions TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            INSERT INTO assistant_personas VALUES
                (1, '账小喵', '🐱', 'playful', 5, 'cute', 'short', 2, 1, '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """
        )
        _upgrade_persona_schema(conn)
        row = conn.execute("SELECT * FROM assistant_personas WHERE user_id = 1").fetchone()
        columns = [item["name"] for item in conn.execute("PRAGMA table_info(assistant_personas)")]
        self.assertEqual(row["mode"], "witty_dark")
        self.assertNotIn("snark_level", columns)
        conn.close()


if __name__ == "__main__":
    unittest.main()
