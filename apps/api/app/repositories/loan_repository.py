from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.core.database import transaction
from app.domain.schemas import LoanCreate, LoanRead, LoanUpdate


def _row_to_loan(row: Any) -> LoanRead:
    return LoanRead(
        id=row["id"], ledger_id=row["ledger_id"], creditor=row["creditor"],
        borrowed_at=date.fromisoformat(row["borrowed_at"]), principal=Decimal(row["principal"]),
        repayment_months=row["repayment_months"], annual_rate=Decimal(row["annual_rate"]),
        repayment_method=row["repayment_method"], first_payment_date=date.fromisoformat(row["first_payment_date"]),
        note=row["note"], created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class LoanRepository:
    def list(self, ledger_id: int) -> list[LoanRead]:
        with transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM loans WHERE ledger_id = ? ORDER BY borrowed_at DESC, id DESC", (ledger_id,)
            ).fetchall()
        return [_row_to_loan(row) for row in rows]

    def create(self, payload: LoanCreate, ledger_id: int) -> LoanRead:
        with transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO loans
                (ledger_id, creditor, borrowed_at, principal, repayment_months, annual_rate,
                 repayment_method, first_payment_date, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ledger_id, payload.creditor, payload.borrowed_at.isoformat(), str(payload.principal),
                 payload.repayment_months, str(payload.annual_rate), payload.repayment_method,
                 payload.first_payment_date.isoformat(), payload.note),
            )
            row = conn.execute("SELECT * FROM loans WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_loan(row)

    def update(self, loan_id: int, ledger_id: int, payload: LoanUpdate) -> LoanRead | None:
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            with transaction() as conn:
                row = conn.execute("SELECT * FROM loans WHERE id = ? AND ledger_id = ?", (loan_id, ledger_id)).fetchone()
            return _row_to_loan(row) if row else None
        values: list[Any] = []
        assignments = []
        for key, value in changes.items():
            assignments.append(f"{key} = ?")
            values.append(value.isoformat() if isinstance(value, date) else str(value) if isinstance(value, Decimal) else value)
        assignments.append("updated_at = CURRENT_TIMESTAMP")
        values.extend([loan_id, ledger_id])
        with transaction() as conn:
            conn.execute(f"UPDATE loans SET {', '.join(assignments)} WHERE id = ? AND ledger_id = ?", values)
            row = conn.execute("SELECT * FROM loans WHERE id = ? AND ledger_id = ?", (loan_id, ledger_id)).fetchone()
        return _row_to_loan(row) if row else None

    def delete(self, loan_id: int, ledger_id: int) -> bool:
        with transaction() as conn:
            cursor = conn.execute("DELETE FROM loans WHERE id = ? AND ledger_id = ?", (loan_id, ledger_id))
        return cursor.rowcount > 0
