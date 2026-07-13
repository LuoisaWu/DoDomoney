from app.domain.schemas import BudgetCreate, BudgetRead
from app.repositories.budget_repository import BudgetRepository


class BudgetService:
    def __init__(self, repository: BudgetRepository | None = None) -> None:
        self.repository = repository or BudgetRepository()

    def list_budgets(self) -> list[BudgetRead]:
        return self.repository.list_budgets()

    def create_budget(self, payload: BudgetCreate) -> BudgetRead:
        return self.repository.create_budget(payload)
