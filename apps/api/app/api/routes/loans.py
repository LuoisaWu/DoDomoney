from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import RequestContext, get_request_context
from app.domain.schemas import LoanCreate, LoanRead, LoanUpdate
from app.repositories.loan_repository import LoanRepository

router = APIRouter()
repository = LoanRepository()


@router.get("", response_model=list[LoanRead])
def list_loans(context: RequestContext = Depends(get_request_context)) -> list[LoanRead]:
    return repository.list(context.ledger.id)


@router.post("", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(payload: LoanCreate, context: RequestContext = Depends(get_request_context)) -> LoanRead:
    return repository.create(payload, context.ledger.id)


@router.patch("/{loan_id}", response_model=LoanRead)
def update_loan(loan_id: int, payload: LoanUpdate, context: RequestContext = Depends(get_request_context)) -> LoanRead:
    loan = repository.update(loan_id, context.ledger.id, payload)
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(loan_id: int, context: RequestContext = Depends(get_request_context)) -> None:
    if not repository.delete(loan_id, context.ledger.id):
        raise HTTPException(status_code=404, detail="Loan not found")
