from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import RequestContext, get_request_context
from app.domain.schemas import AssistantPersonaRead, AssistantPersonaUpdate, UserCreate, UserRead, UserUpdate
from app.services.identity_service import IdentityService
from app.services.persona_service import PersonaService

router = APIRouter()
identity_service = IdentityService()
persona_service = PersonaService()


@router.get("", response_model=list[UserRead])
def list_users() -> list[UserRead]:
    return identity_service.list_users()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> UserRead:
    try:
        return identity_service.create_user(payload)
    except Exception as exc:
        raise HTTPException(status_code=409, detail="User already exists or cannot be created") from exc


@router.patch("/me", response_model=UserRead)
def update_current_user(
    payload: UserUpdate,
    context: RequestContext = Depends(get_request_context),
) -> UserRead:
    return identity_service.update_user(context.user.id, payload)


@router.get("/me/persona", response_model=AssistantPersonaRead)
def get_persona(context: RequestContext = Depends(get_request_context)) -> AssistantPersonaRead:
    return persona_service.get(context.user.id)


@router.put("/me/persona", response_model=AssistantPersonaRead)
def update_persona(
    payload: AssistantPersonaUpdate,
    context: RequestContext = Depends(get_request_context),
) -> AssistantPersonaRead:
    return persona_service.update(context.user.id, payload)
