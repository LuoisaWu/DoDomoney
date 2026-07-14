from enum import StrEnum


class EntryType(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"


class AssistantTone(StrEnum):
    CUTE = "cute"
    SNARKY = "snarky"
    GENTLE = "gentle"
    ADVISOR = "advisor"
    MINIMAL = "minimal"


class PersonaMode(StrEnum):
    BALANCED = "balanced"
    CUTE = "cute"
    RATIONAL = "rational"
    ENCOURAGING = "encouraging"
    WITTY_DARK = "witty_dark"


class VoiceStyle(StrEnum):
    WARM = "warm"
    PLAYFUL = "playful"
    DIRECT = "direct"
    CALM = "calm"


class LedgerType(StrEnum):
    PERSONAL = "personal"
    FAMILY = "family"
    SHARED = "shared"


class LedgerRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
