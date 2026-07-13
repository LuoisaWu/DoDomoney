from dataclasses import dataclass

from fastapi import Header, HTTPException
from app.core.auth import token_digest

from app.domain.schemas import LedgerRead, UserRead
from app.services.identity_service import IdentityService

identity_service = IdentityService()


@dataclass(frozen=True)
class RequestContext:
    user: UserRead
    ledger: LedgerRead


def get_request_context(
    authorization: str | None = Header(default=None),
    x_dodomoney_user_id: int | None = Header(default=None),
    x_dodomoney_ledger_id: int | None = Header(default=None),
) -> RequestContext:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    user = identity_service.repository.get_user_by_session(
        token_digest(authorization.removeprefix("Bearer ").strip())
    )
    if user is None:
        raise HTTPException(status_code=401, detail="登录状态已失效")
    if x_dodomoney_user_id is not None and x_dodomoney_user_id != user.id:
        raise HTTPException(status_code=403, detail="用户身份不匹配")

    ledgers = identity_service.list_ledgers(user.id)
    if not ledgers:
        raise HTTPException(status_code=403, detail="User has no ledgers")

    if x_dodomoney_ledger_id is None:
        ledger = ledgers[0]
    else:
        ledger = identity_service.get_ledger_for_user(x_dodomoney_ledger_id, user.id)
        if ledger is None:
            raise HTTPException(status_code=403, detail="Ledger is not available for this user")

    return RequestContext(user=user, ledger=ledger)
