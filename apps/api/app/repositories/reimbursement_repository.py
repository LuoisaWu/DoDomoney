from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.core.database import transaction
from app.domain.schemas import ReimbursementCreate, ReimbursementRead, ReimbursementUpdate


def _row_to_reimbursement(row: Any) -> ReimbursementRead:
    return ReimbursementRead(
        id=row["id"], ledger_id=row["ledger_id"], merchant=row["merchant"],
        invoice_title=row["invoice_title"],
        amount=Decimal(row["amount"]), invoice_date=date.fromisoformat(row["invoice_date"]),
        category=row["category"], invoice_number=row["invoice_number"], status=row["status"],
        note=row["note"], image_url=row["image_url"],
        created_at=datetime.fromisoformat(row["created_at"]), updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class ReimbursementRepository:
    def list(self, ledger_id: int) -> list[ReimbursementRead]:
        with transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM reimbursements WHERE ledger_id = ? ORDER BY invoice_date DESC, id DESC", (ledger_id,)
            ).fetchall()
        return [_row_to_reimbursement(row) for row in rows]

    def create(self, payload: ReimbursementCreate, ledger_id: int) -> ReimbursementRead:
        with transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO reimbursements
                (ledger_id, merchant, invoice_title, amount, invoice_date, category, invoice_number, status, note, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ledger_id, payload.merchant, payload.invoice_title, str(payload.amount), payload.invoice_date.isoformat(), payload.category,
                 payload.invoice_number, payload.status, payload.note, payload.image_url),
            )
            row = conn.execute("SELECT * FROM reimbursements WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_reimbursement(row)

    def update(self, item_id: int, ledger_id: int, payload: ReimbursementUpdate) -> ReimbursementRead | None:
        values = payload.model_dump(exclude_unset=True)
        if not values:
            with transaction() as conn:
                row = conn.execute("SELECT * FROM reimbursements WHERE id = ? AND ledger_id = ?", (item_id, ledger_id)).fetchone()
            return _row_to_reimbursement(row) if row else None
        assignments = []
        params = []
        for key, value in values.items():
            assignments.append(f"{key} = ?")
            params.append(value.isoformat() if isinstance(value, date) else str(value) if isinstance(value, Decimal) else value)
        assignments.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([item_id, ledger_id])
        with transaction() as conn:
            conn.execute(f"UPDATE reimbursements SET {', '.join(assignments)} WHERE id = ? AND ledger_id = ?", params)
            row = conn.execute("SELECT * FROM reimbursements WHERE id = ? AND ledger_id = ?", (item_id, ledger_id)).fetchone()
        return _row_to_reimbursement(row) if row else None

    def delete(self, item_id: int, ledger_id: int) -> bool:
        with transaction() as conn:
            cursor = conn.execute("DELETE FROM reimbursements WHERE id = ? AND ledger_id = ?", (item_id, ledger_id))
        return cursor.rowcount > 0
