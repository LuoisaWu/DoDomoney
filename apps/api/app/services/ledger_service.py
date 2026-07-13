from app.domain.schemas import EntryCreate, EntryRead, EntryUpdate
from app.repositories.entry_repository import EntryRepository


class LedgerService:
    def __init__(self, repository: EntryRepository | None = None) -> None:
        self.repository = repository or EntryRepository()

    def list_entries(self, ledger_id: int, limit: int = 100, offset: int = 0) -> list[EntryRead]:
        return self.repository.list_entries(ledger_id=ledger_id, limit=limit, offset=offset)

    def create_entry(self, payload: EntryCreate, ledger_id: int) -> EntryRead:
        return self.repository.create_entry(payload, ledger_id=ledger_id)

    def update_entry(self, entry_id: int, ledger_id: int, payload: EntryUpdate) -> EntryRead | None:
        return self.repository.update_entry(entry_id, ledger_id, payload)

    def delete_entry(self, entry_id: int, ledger_id: int) -> bool:
        return self.repository.delete_entry(entry_id, ledger_id)

    def monthly_summary(self, ledger_id: int, month: str):
        return self.repository.monthly_summary(ledger_id, month)

    def list_preferences(self, user_id: int):
        return self.repository.list_preferences(user_id)

    def save_preference(self, user_id: int, keyword: str, category: str, subcategory: str | None):
        return self.repository.save_preference(user_id, keyword, category, subcategory)
