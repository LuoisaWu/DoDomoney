import json
from datetime import datetime

from app.core.database import transaction
from app.domain.schemas import ChatMessageRead, ParsedTransaction


class ChatRepository:
    def list_messages(self, ledger_id: int, user_id: int, limit: int = 200) -> list[ChatMessageRead]:
        with transaction() as conn:
            rows = conn.execute(
                """
                SELECT * FROM (
                    SELECT * FROM chat_messages
                    WHERE ledger_id = ? AND user_id = ?
                    ORDER BY id DESC LIMIT ?
                ) ORDER BY id ASC
                """,
                (ledger_id, user_id, limit),
            ).fetchall()
        return [self._to_message(row) for row in rows]

    def add_message(
        self,
        ledger_id: int,
        user_id: int,
        role: str,
        content: str,
        parsed: ParsedTransaction | None = None,
        recorded: bool = False,
    ) -> ChatMessageRead:
        parsed_json = json.dumps(parsed.model_dump(mode="json"), ensure_ascii=False) if parsed else None
        with transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO chat_messages (ledger_id, user_id, role, content, parsed_json, recorded)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (ledger_id, user_id, role, content, parsed_json, int(recorded)),
            )
            row = conn.execute("SELECT * FROM chat_messages WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self._to_message(row)

    def clear_messages(self, ledger_id: int, user_id: int) -> None:
        with transaction() as conn:
            conn.execute(
                "DELETE FROM chat_messages WHERE ledger_id = ? AND user_id = ?",
                (ledger_id, user_id),
            )

    @staticmethod
    def _to_message(row) -> ChatMessageRead:
        parsed = ParsedTransaction.model_validate_json(row["parsed_json"]) if row["parsed_json"] else None
        return ChatMessageRead(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            parsed=parsed,
            recorded=bool(row["recorded"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
