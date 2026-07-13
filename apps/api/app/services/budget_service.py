from app.domain.schemas import BudgetCreate, BudgetRead, BudgetUpdate
from app.repositories.budget_repository import BudgetRepository


class BudgetService:
    def __init__(self, repository: BudgetRepository | None = None) -> None:
        self.repository = repository or BudgetRepository()

    def list_budgets(self, ledger_id: int) -> list[BudgetRead]:
        return self.repository.list_budgets(ledger_id)

    def create_budget(self, payload: BudgetCreate, ledger_id: int) -> BudgetRead:
        return self.repository.create_budget(payload, ledger_id)

    def update_budget(self, budget_id: int, ledger_id: int, payload: BudgetUpdate) -> BudgetRead | None:
        return self.repository.update_budget(budget_id, ledger_id, payload)

    def delete_budget(self, budget_id: int, ledger_id: int) -> bool:
        return self.repository.delete_budget(budget_id, ledger_id)
