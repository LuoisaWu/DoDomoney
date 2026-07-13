from app.domain.schemas import EntryCreate, EntryRead, EntryUpdate
from app.repositories.entry_repository import EntryRepository


class LedgerService:
    def __init__(self, repository: EntryRepository | None = None) -> None:
        self.repository = repository or EntryRepository()

    def list_entries(self, limit: int = 100, offset: int = 0) -> list[EntryRead]:
        return self.repository.list_entries(limit=limit, offset=offset)

    def create_entry(self, payload: EntryCreate) -> EntryRead:
        return self.repository.create_entry(payload)

    def update_entry(self, entry_id: int, payload: EntryUpdate) -> EntryRead | None:
        return self.repository.update_entry(entry_id, payload)

    def delete_entry(self, entry_id: int) -> bool:
        return self.repository.delete_entry(entry_id)
