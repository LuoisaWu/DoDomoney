from app.domain.schemas import (
    LedgerCreate,
    LedgerMemberCreate,
    LedgerMemberRead,
    LedgerRead,
    LoginResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.repositories.identity_repository import IdentityRepository
from app.core.auth import hash_password, new_session_token, token_digest, verify_password


class IdentityService:
    def __init__(self, repository: IdentityRepository | None = None) -> None:
        self.repository = repository or IdentityRepository()

    def default_context(self) -> tuple[UserRead, LedgerRead]:
        return self.repository.get_default_context()

    def create_user(self, payload: UserCreate) -> UserRead:
        return self.repository.create_user(payload)

    def list_users(self) -> list[UserRead]:
        return self.repository.list_users()

    def update_user(self, user_id: int, payload: UserUpdate) -> UserRead:
        return self.repository.update_user(user_id, payload)

    def _login_response(self, user: UserRead) -> LoginResponse:
        ledgers = self.repository.list_ledgers(user.id)
        token = new_session_token()
        self.repository.create_session(user.id, token_digest(token))
        return LoginResponse(user=user, ledgers=ledgers, active_ledger_id=ledgers[0].id, token=token)

    def register(self, email: str, display_name: str, password: str) -> LoginResponse:
        existing = self.repository.get_user_by_email(email)
        if existing and self.repository.get_password_hash(email):
            raise ValueError("该邮箱已注册，请直接登录")
        user = existing or self.repository.create_user(
            UserCreate(email=email, display_name=display_name)
        )
        if existing and existing.display_name != display_name.strip():
            user = self.repository.update_user(existing.id, UserUpdate(display_name=display_name))
        self.repository.set_password_hash(user.id, hash_password(password))
        return self._login_response(user)

    def login(self, email: str, password: str) -> LoginResponse:
        user = self.repository.get_user_by_email(email)
        if user is None or not verify_password(password, self.repository.get_password_hash(email)):
            raise ValueError("邮箱或密码不正确")
        return self._login_response(user)

    def restore_session(self, token: str) -> LoginResponse:
        user = self.repository.get_user_by_session(token_digest(token))
        if user is None:
            raise ValueError("登录状态已失效")
        ledgers = self.repository.list_ledgers(user.id)
        return LoginResponse(user=user, ledgers=ledgers, active_ledger_id=ledgers[0].id, token=token)

    def logout(self, token: str) -> None:
        self.repository.delete_session(token_digest(token))

    def list_ledgers(self, user_id: int) -> list[LedgerRead]:
        return self.repository.list_ledgers(user_id)

    def get_ledger_for_user(self, ledger_id: int, user_id: int) -> LedgerRead | None:
        return self.repository.get_ledger_for_user(ledger_id, user_id)

    def create_ledger(self, user_id: int, payload: LedgerCreate) -> LedgerRead:
        return self.repository.create_ledger(user_id, payload)

    def list_members(self, ledger_id: int, user_id: int) -> list[LedgerMemberRead]:
        return self.repository.list_members(ledger_id, user_id)

    def add_member(self, ledger_id: int, actor_user_id: int, payload: LedgerMemberCreate) -> LedgerMemberRead | None:
        return self.repository.add_member(ledger_id, actor_user_id, payload)
