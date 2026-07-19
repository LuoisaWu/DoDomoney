from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import RequestContext, get_request_context
from app.domain.schemas import ReimbursementCreate, ReimbursementRead, ReimbursementUpdate
from app.repositories.reimbursement_repository import ReimbursementRepository

router = APIRouter()
repository = ReimbursementRepository()


@router.get("", response_model=list[ReimbursementRead])
def list_reimbursements(context: RequestContext = Depends(get_request_context)) -> list[ReimbursementRead]:
    return repository.list(context.ledger.id)


@router.post("", response_model=ReimbursementRead, status_code=status.HTTP_201_CREATED)
def create_reimbursement(payload: ReimbursementCreate, context: RequestContext = Depends(get_request_context)) -> ReimbursementRead:
    return repository.create(payload, context.ledger.id)


@router.patch("/{item_id}", response_model=ReimbursementRead)
def update_reimbursement(item_id: int, payload: ReimbursementUpdate, context: RequestContext = Depends(get_request_context)) -> ReimbursementRead:
    item = repository.update(item_id, context.ledger.id, payload)
    if item is None:
        raise HTTPException(status_code=404, detail="报销记录不存在。")
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reimbursement(item_id: int, context: RequestContext = Depends(get_request_context)) -> None:
    if not repository.delete(item_id, context.ledger.id):
        raise HTTPException(status_code=404, detail="报销记录不存在。")
