from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import RequestContext, get_request_context
from app.domain.schemas import LedgerCreate, LedgerMemberCreate, LedgerMemberRead, LedgerRead
from app.services.identity_service import IdentityService

router = APIRouter()
identity_service = IdentityService()


@router.get("", response_model=list[LedgerRead])
def list_ledgers(context: RequestContext = Depends(get_request_context)) -> list[LedgerRead]:
    return identity_service.list_ledgers(context.user.id)


@router.post("", response_model=LedgerRead, status_code=status.HTTP_201_CREATED)
def create_ledger(
    payload: LedgerCreate,
    context: RequestContext = Depends(get_request_context),
) -> LedgerRead:
    return identity_service.create_ledger(context.user.id, payload)


@router.get("/{ledger_id}/members", response_model=list[LedgerMemberRead])
def list_members(
    ledger_id: int,
    context: RequestContext = Depends(get_request_context),
) -> list[LedgerMemberRead]:
    members = identity_service.list_members(ledger_id, context.user.id)
    if not members:
        raise HTTPException(status_code=404, detail="Ledger not found")
    return members


@router.post("/{ledger_id}/members", response_model=LedgerMemberRead, status_code=status.HTTP_201_CREATED)
def add_member(
    ledger_id: int,
    payload: LedgerMemberCreate,
    context: RequestContext = Depends(get_request_context),
) -> LedgerMemberRead:
    member = identity_service.add_member(ledger_id, context.user.id, payload)
    if member is None:
        raise HTTPException(status_code=403, detail="Only ledger owners or admins can add members")
    return member
