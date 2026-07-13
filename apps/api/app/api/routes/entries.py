from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import RequestContext, get_request_context
from datetime import date

from app.domain.schemas import EntryCreate, EntryRead, EntryUpdate, MonthlySummary, PeriodAnalysis, PreferenceCreate, PreferenceRead
from app.services.analysis_service import AnalysisService
from app.services.ledger_service import LedgerService

router = APIRouter()
ledger_service = LedgerService()
analysis_service = AnalysisService()


@router.get("", response_model=list[EntryRead])
def list_entries(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    context: RequestContext = Depends(get_request_context),
) -> list[EntryRead]:
    return ledger_service.list_entries(ledger_id=context.ledger.id, limit=limit, offset=offset)


@router.get("/summary", response_model=MonthlySummary)
def monthly_summary(
    month: str = Query(pattern=r"^\d{4}-\d{2}$"),
    context: RequestContext = Depends(get_request_context),
) -> MonthlySummary:
    raw = ledger_service.monthly_summary(context.ledger.id, month)
    expense = raw["expense_total"]
    categories = [
        {"category": row["category"], "amount": row["amount"], "percentage": round(float(row["amount"]) / float(expense) * 100, 1) if expense else 0}
        for row in raw["categories"]
    ]
    return MonthlySummary(month=month, expense_total=expense, income_total=raw["income_total"], balance=raw["income_total"] - expense, entry_count=raw["count"], categories=categories)


@router.get("/analysis", response_model=PeriodAnalysis)
def period_analysis(
    start_date: date,
    end_date: date,
    include_ai: bool = False,
    context: RequestContext = Depends(get_request_context),
) -> PeriodAnalysis:
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="结束日期不能早于开始日期")
    if (end_date - start_date).days > 365:
        raise HTTPException(status_code=422, detail="单次最多分析 366 天")
    return analysis_service.analyze(context.ledger.id, start_date, end_date, include_ai)


@router.get("/preferences", response_model=list[PreferenceRead])
def list_preferences(context: RequestContext = Depends(get_request_context)) -> list[PreferenceRead]:
    return [PreferenceRead(**item) for item in ledger_service.list_preferences(context.user.id)]


@router.post("/preferences", response_model=PreferenceRead)
def save_preference(payload: PreferenceCreate, context: RequestContext = Depends(get_request_context)) -> PreferenceRead:
    return PreferenceRead(**ledger_service.save_preference(context.user.id, payload.keyword, payload.category, payload.subcategory))


@router.post("", response_model=EntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(payload: EntryCreate, context: RequestContext = Depends(get_request_context)) -> EntryRead:
    return ledger_service.create_entry(payload, context.ledger.id)


@router.patch("/{entry_id}", response_model=EntryRead)
def update_entry(entry_id: int, payload: EntryUpdate, context: RequestContext = Depends(get_request_context)) -> EntryRead:
    entry = ledger_service.update_entry(entry_id, context.ledger.id, payload)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, context: RequestContext = Depends(get_request_context)) -> None:
    deleted = ledger_service.delete_entry(entry_id, context.ledger.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
