from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.database import transaction
from app.domain.schemas import EntryCreate, EntryRead, EntryUpdate


def _row_to_entry(row: Any) -> EntryRead:
    return EntryRead(
        id=row["id"],
        type=row["type"],
        amount=Decimal(str(row["amount"])),
        category=row["category"],
        subcategory=row["subcategory"],
        description=row["description"],
        occurred_at=datetime.fromisoformat(row["occurred_at"]),
        raw_text=row["raw_text"],
        source=row["source"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class EntryRepository:
    def list_entries(self, limit: int = 100, offset: int = 0) -> list[EntryRead]:
        with transaction() as conn:
            rows = conn.execute(
                """
                SELECT * FROM entries
                ORDER BY occurred_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [_row_to_entry(row) for row in rows]

    def get_entry(self, entry_id: int) -> EntryRead | None:
        with transaction() as conn:
            row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        return _row_to_entry(row) if row else None

    def create_entry(self, payload: EntryCreate) -> EntryRead:
        with transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO entries (
                    type, amount, category, subcategory, description,
                    occurred_at, raw_text, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.type,
                    str(payload.amount),
                    payload.category,
                    payload.subcategory,
                    payload.description,
                    payload.occurred_at.isoformat(),
                    payload.raw_text,
                    payload.source,
                ),
            )
            row = conn.execute("SELECT * FROM entries WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_entry(row)

    def update_entry(self, entry_id: int, payload: EntryUpdate) -> EntryRead | None:
        existing = self.get_entry(entry_id)
        if existing is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return existing

        columns = []
        values = []
        for key, value in update_data.items():
            columns.append(f"{key} = ?")
            if isinstance(value, datetime):
                values.append(value.isoformat())
            else:
                values.append(str(value) if isinstance(value, Decimal) else value)

        columns.append("updated_at = CURRENT_TIMESTAMP")
        values.append(entry_id)

        with transaction() as conn:
            conn.execute(f"UPDATE entries SET {', '.join(columns)} WHERE id = ?", values)
            row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        return _row_to_entry(row)

    def delete_entry(self, entry_id: int) -> bool:
        with transaction() as conn:
            cursor = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        return cursor.rowcount > 0

    def monthly_summary(self, month: str) -> dict[str, Any]:
        with transaction() as conn:
            totals = conn.execute(
                "SELECT type, COALESCE(SUM(CAST(amount AS REAL)), 0) AS total, COUNT(*) AS count FROM entries WHERE substr(occurred_at, 1, 7) = ? GROUP BY type",
                (month,),
            ).fetchall()
            categories = conn.execute(
                "SELECT category, COALESCE(SUM(CAST(amount AS REAL)), 0) AS amount FROM entries WHERE substr(occurred_at, 1, 7) = ? AND type = 'expense' GROUP BY category ORDER BY amount DESC",
                (month,),
            ).fetchall()
        expense = next((float(row["total"]) for row in totals if row["type"] == "expense"), 0.0)
        income = next((float(row["total"]) for row in totals if row["type"] == "income"), 0.0)
        return {"expense_total": Decimal(str(expense)), "income_total": Decimal(str(income)), "count": sum(int(row["count"]) for row in totals), "categories": categories}

    def list_preferences(self) -> list[dict[str, Any]]:
        with transaction() as conn:
            rows = conn.execute("SELECT * FROM category_preferences ORDER BY hit_count DESC, updated_at DESC").fetchall()
        return [dict(row) for row in rows]

    def save_preference(self, keyword: str, category: str, subcategory: str | None) -> dict[str, Any]:
        with transaction() as conn:
            conn.execute(
                "INSERT INTO category_preferences (keyword, category, subcategory) VALUES (?, ?, ?) ON CONFLICT(keyword, category, subcategory) DO UPDATE SET hit_count = hit_count + 1, updated_at = CURRENT_TIMESTAMP",
                (keyword, category, subcategory),
            )
            row = conn.execute("SELECT * FROM category_preferences WHERE keyword = ? AND category = ? AND subcategory IS ?", (keyword, category, subcategory)).fetchone()
        return dict(row)
