from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.core.database import transaction
from app.domain.schemas import BudgetCreate, BudgetRead, BudgetUpdate


def _row_to_budget(row: Any) -> BudgetRead:
    return BudgetRead(
        id=row["id"],
        month=date.fromisoformat(row["month"]),
        amount=Decimal(str(row["amount"])),
        category=row["category"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class BudgetRepository:
    def list_budgets(self) -> list[BudgetRead]:
        with transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM budgets ORDER BY month DESC, category ASC"
            ).fetchall()
        return [_row_to_budget(row) for row in rows]

    def create_budget(self, payload: BudgetCreate) -> BudgetRead:
        with transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO budgets (month, amount, category)
                VALUES (?, ?, ?)
                """,
                (payload.month.isoformat(), str(payload.amount), payload.category),
            )
            row = conn.execute("SELECT * FROM budgets WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_budget(row)

    def update_budget(self, budget_id: int, payload: BudgetUpdate) -> BudgetRead | None:
        with transaction() as conn:
            if payload.amount is not None:
                conn.execute("UPDATE budgets SET amount = ? WHERE id = ?", (str(payload.amount), budget_id))
            row = conn.execute("SELECT * FROM budgets WHERE id = ?", (budget_id,)).fetchone()
        return _row_to_budget(row) if row else None

    def delete_budget(self, budget_id: int) -> bool:
        with transaction() as conn:
            cursor = conn.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        return cursor.rowcount > 0
