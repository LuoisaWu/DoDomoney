from fastapi import APIRouter, HTTPException, Query, status

from app.domain.schemas import EntryCreate, EntryRead, EntryUpdate
from app.services.ledger_service import LedgerService

router = APIRouter()
ledger_service = LedgerService()


@router.get("", response_model=list[EntryRead])
def list_entries(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[EntryRead]:
    return ledger_service.list_entries(limit=limit, offset=offset)


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
