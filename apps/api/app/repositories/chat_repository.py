import json
from datetime import datetime

from app.core.database import transaction
from app.domain.schemas import ChatMessageRead, ParsedLoan, ParsedReimbursement, ParsedTransaction


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
        parsed_loan: ParsedLoan | None = None,
        parsed_reimbursement: ParsedReimbursement | None = None,
        image_url: str | None = None,
        recorded: bool = False,
    ) -> ChatMessageRead:
        parsed_data = None
        if parsed_reimbursement:
            parsed_data = {"kind": "reimbursement", "data": parsed_reimbursement.model_dump(mode="json")}
        elif parsed_loan:
            parsed_data = {"kind": "loan", "data": parsed_loan.model_dump(mode="json")}
        elif parsed:
            parsed_data = {"kind": "transaction", "data": parsed.model_dump(mode="json")}
        parsed_json = json.dumps(parsed_data, ensure_ascii=False) if parsed_data else None
        with transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO chat_messages (ledger_id, user_id, role, content, parsed_json, recorded, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (ledger_id, user_id, role, content, parsed_json, int(recorded), image_url),
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
        parsed = None
        parsed_loan = None
        parsed_reimbursement = None
        if row["parsed_json"]:
            data = json.loads(row["parsed_json"])
            if data.get("kind") == "loan":
                parsed_loan = ParsedLoan.model_validate(data["data"])
            elif data.get("kind") == "reimbursement":
                parsed_reimbursement = ParsedReimbursement.model_validate(data["data"])
            elif data.get("kind") == "transaction":
                parsed = ParsedTransaction.model_validate(data["data"])
            else:
                # Backward compatibility with messages stored before typed contexts.
                parsed = ParsedTransaction.model_validate(data)
        return ChatMessageRead(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            parsed=parsed,
            parsed_loan=parsed_loan,
            parsed_reimbursement=parsed_reimbursement,
            image_url=row["image_url"] if "image_url" in row.keys() else None,
            recorded=bool(row["recorded"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
