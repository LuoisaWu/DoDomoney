from fastapi import APIRouter, HTTPException, status

from app.domain.schemas import BudgetCreate, BudgetRead, BudgetUpdate
from app.services.budget_service import BudgetService

router = APIRouter()
budget_service = BudgetService()


@router.get("", response_model=list[BudgetRead])
def list_budgets() -> list[BudgetRead]:
    return budget_service.list_budgets()


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(payload: BudgetCreate) -> BudgetRead:
    return budget_service.create_budget(payload)


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(budget_id: int, payload: BudgetUpdate) -> BudgetRead:
    budget = budget_service.update_budget(budget_id, payload)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int) -> None:
    if not budget_service.delete_budget(budget_id):
        raise HTTPException(status_code=404, detail="Budget not found")
