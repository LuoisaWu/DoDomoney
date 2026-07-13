from app.domain.schemas import AssistantPersonaRead, AssistantPersonaUpdate
from app.repositories.persona_repository import PersonaRepository


class PersonaService:
    def __init__(self, repository: PersonaRepository | None = None) -> None:
        self.repository = repository or PersonaRepository()

    def get(self, user_id: int) -> AssistantPersonaRead:
        return self.repository.get_for_user(user_id)

    def update(self, user_id: int, payload: AssistantPersonaUpdate) -> AssistantPersonaRead:
        return self.repository.update_for_user(user_id, payload)
