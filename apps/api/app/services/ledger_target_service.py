import re
from dataclasses import dataclass

from app.domain.schemas import LedgerRead


@dataclass(frozen=True)
class LedgerDirective:
    ledger_name: str
    remaining_message: str


_NAME = r"[^\s，。,.！？!?；;：:'\"“”]{1,40}"
_PATTERNS = (
    re.compile(rf"(?:请)?(?:把|将)?\s*(?:这笔|该笔)?(?:账|费用|借款|报销)?\s*(?:记录|登记|记|计|放|归)(?:入|到|进)\s*[‘'\"“]?\s*(?P<name>{_NAME})\s*[’'\"”]?\s*(?:账本|帐本)(?:里|中)?"),
    re.compile(rf"(?:在|用)\s*[‘'\"“]?\s*(?P<name>{_NAME})\s*[’'\"”]?\s*(?:账本|帐本)(?:里|中)?\s*(?:记录|登记|记)"),
)


def extract_ledger_directive(message: str) -> LedgerDirective | None:
    for pattern in _PATTERNS:
        match = pattern.search(message)
        if not match:
            continue
        name = match.group("name").strip()
        remaining = f"{message[:match.start()]} {message[match.end():]}"
        remaining = re.sub(r"^[\s，。,.；;：:]+|[\s，。,.；;：:]+$", "", remaining)
        return LedgerDirective(ledger_name=name, remaining_message=remaining)
    return None


def _normalized(value: str) -> str:
    return re.sub(r"\s+", "", value).removesuffix("账本").removesuffix("帐本").casefold()


def find_accessible_ledger(name: str, ledgers: list[LedgerRead]) -> LedgerRead | None:
    target = _normalized(name)
    exact = next((ledger for ledger in ledgers if _normalized(ledger.name) == target), None)
    if exact:
        return exact
    if target.startswith("我的"):
        shortened = target.removeprefix("我的")
        return next((ledger for ledger in ledgers if _normalized(ledger.name) == shortened), None)
    return None
