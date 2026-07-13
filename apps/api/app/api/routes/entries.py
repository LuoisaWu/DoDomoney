from fastapi import APIRouter, HTTPException, Query, status

from app.domain.schemas import EntryCreate, EntryRead, EntryUpdate, MonthlySummary, PreferenceCreate, PreferenceRead
from app.services.ledger_service import LedgerService

router = APIRouter()
ledger_service = LedgerService()


@router.get("", response_model=list[EntryRead])
def list_entries(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[EntryRead]:
    return ledger_service.list_entries(limit=limit, offset=offset)


@router.get("/summary", response_model=MonthlySummary)
def monthly_summary(month: str = Query(pattern=r"^\d{4}-\d{2}$")) -> MonthlySummary:
    raw = ledger_service.monthly_summary(month)
    expense = raw["expense_total"]
    categories = [
        {"category": row["category"], "amount": row["amount"], "percentage": round(float(row["amount"]) / float(expense) * 100, 1) if expense else 0}
        for row in raw["categories"]
    ]
    return MonthlySummary(month=month, expense_total=expense, income_total=raw["income_total"], balance=raw["income_total"] - expense, entry_count=raw["count"], categories=categories)


@router.get("/preferences", response_model=list[PreferenceRead])
def list_preferences() -> list[PreferenceRead]:
    return [PreferenceRead(**item) for item in ledger_service.list_preferences()]


@router.post("/preferences", response_model=PreferenceRead)
def save_preference(payload: PreferenceCreate) -> PreferenceRead:
    return PreferenceRead(**ledger_service.save_preference(payload.keyword, payload.category, payload.subcategory))


@router.post("", response_model=EntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(payload: EntryCreate) -> EntryRead:
    return ledger_service.create_entry(payload)


@router.patch("/{entry_id}", response_model=EntryRead)
def update_entry(entry_id: int, payload: EntryUpdate) -> EntryRead:
    entry = ledger_service.update_entry(entry_id, payload)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int) -> None:
    deleted = ledger_service.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
