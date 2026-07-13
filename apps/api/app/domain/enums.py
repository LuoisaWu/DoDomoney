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
