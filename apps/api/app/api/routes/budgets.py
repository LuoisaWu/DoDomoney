from fastapi import APIRouter, status

from app.domain.schemas import BudgetCreate, BudgetRead
from app.services.budget_service import BudgetService

router = APIRouter()
budget_service = BudgetService()


@router.get("", response_model=list[BudgetRead])
def list_budgets() -> list[BudgetRead]:
    return budget_service.list_budgets()


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(payload: BudgetCreate) -> BudgetRead:
    return budget_service.create_budget(payload)
