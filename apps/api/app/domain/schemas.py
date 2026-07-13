from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.enums import AssistantTone, EntryType


class EntryBase(BaseModel):
    type: EntryType
    amount: Decimal = Field(gt=0)
    category: str = Field(min_length=1, max_length=80)
    subcategory: Optional[str] = Field(default=None, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    occurred_at: datetime


class EntryCreate(EntryBase):
    raw_text: Optional[str] = None
    source: str = "manual"


class EntryUpdate(BaseModel):
    type: Optional[EntryType] = None
    amount: Optional[Decimal] = Field(default=None, gt=0)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None


class EntryRead(EntryBase):
    id: int
    raw_text: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: datetime


class ChatRecordRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    assistant_tone: AssistantTone = AssistantTone.CUTE


class ParsedEntry(EntryBase):
    confidence: float = Field(ge=0, le=1)


class ChatRecordResponse(BaseModel):
    assistant_name: str = "账小喵"
    reply: str
    entry: EntryRead
    parsed: ParsedEntry


class BudgetCreate(BaseModel):
    month: date
    amount: Decimal = Field(gt=0)
    category: Optional[str] = None


class BudgetUpdate(BaseModel):
    amount: Optional[Decimal] = Field(default=None, gt=0)


class BudgetRead(BudgetCreate):
    id: int
    created_at: datetime


class CategorySummary(BaseModel):
    category: str
    amount: Decimal
    percentage: float


class MonthlySummary(BaseModel):
    month: str
    expense_total: Decimal
    income_total: Decimal
    balance: Decimal
    entry_count: int
    categories: list[CategorySummary]


class PreferenceCreate(BaseModel):
    keyword: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    subcategory: Optional[str] = None


class PreferenceRead(PreferenceCreate):
    id: int
    hit_count: int
