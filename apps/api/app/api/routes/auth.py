from fastapi import APIRouter, Header, HTTPException, Response, status

from app.domain.schemas import LoginRequest, LoginResponse, RegisterRequest
from app.services.identity_service import IdentityService

router = APIRouter()
identity_service = IdentityService()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    try:
        return identity_service.login(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> LoginResponse:
    try:
        return identity_service.register(payload.email, payload.display_name, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    return authorization.removeprefix("Bearer ").strip()


@router.get("/session", response_model=LoginResponse)
def restore_session(authorization: str | None = Header(default=None)) -> LoginResponse:
    try:
        return identity_service.restore_session(_bearer_token(authorization))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(authorization: str | None = Header(default=None)) -> Response:
    identity_service.logout(_bearer_token(authorization))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
