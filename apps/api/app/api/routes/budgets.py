from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import RequestContext, get_request_context
from app.domain.schemas import BudgetCreate, BudgetRead, BudgetUpdate
from app.services.budget_service import BudgetService

router = APIRouter()
budget_service = BudgetService()


@router.get("", response_model=list[BudgetRead])
def list_budgets(context: RequestContext = Depends(get_request_context)) -> list[BudgetRead]:
    return budget_service.list_budgets(context.ledger.id)


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(payload: BudgetCreate, context: RequestContext = Depends(get_request_context)) -> BudgetRead:
    return budget_service.create_budget(payload, context.ledger.id)


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(budget_id: int, payload: BudgetUpdate, context: RequestContext = Depends(get_request_context)) -> BudgetRead:
    budget = budget_service.update_budget(budget_id, context.ledger.id, payload)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int, context: RequestContext = Depends(get_request_context)) -> None:
    if not budget_service.delete_budget(budget_id, context.ledger.id):
        raise HTTPException(status_code=404, detail="Budget not found")
