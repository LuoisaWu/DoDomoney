from fastapi import APIRouter, Header, HTTPException, Request, Response, status

from app.domain.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    VerificationCodeRequest,
    VerificationCodeResponse,
)
from app.services.identity_service import IdentityService
from app.services.verification_service import (
    VerificationError,
    VerificationService,
    VerificationUnavailableError,
)

router = APIRouter()
identity_service = IdentityService()
verification_service = VerificationService()


def _verify(email: str, purpose: str, code: str) -> None:
    try:
        verification_service.verify(email, purpose, code)
    except VerificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except VerificationUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/verification-code", response_model=VerificationCodeResponse)
def send_verification_code(payload: VerificationCodeRequest, request: Request) -> VerificationCodeResponse:
    try:
        result = verification_service.send_code(
            payload.email,
            "register",
            request.client.host if request.client else "unknown",
        )
        return VerificationCodeResponse(
            message="验证码已发送，请查收邮件",
            retry_after=result.retry_after,
            expires_in=result.expires_in,
            development_code=result.development_code,
        )
    except VerificationError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except VerificationUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    try:
        return identity_service.login(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> LoginResponse:
    try:
        _verify(payload.email, "register", payload.verification_code)
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
