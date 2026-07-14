from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.domain.enums import EntryType, LedgerRole, LedgerType, PersonaMode, VoiceStyle


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    display_name: str = Field(min_length=1, max_length=80)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class UserRead(UserCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class LoginResponse(BaseModel):
    user: UserRead
    ledgers: list["LedgerRead"]
    active_ledger_id: int
    token: str


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class LedgerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: LedgerType = LedgerType.PERSONAL


class LedgerRead(LedgerCreate):
    id: int
    owner_user_id: int
    role: LedgerRole
    member_count: int
    created_at: datetime
    updated_at: datetime


class LedgerMemberCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    display_name: Optional[str] = Field(default=None, max_length=80)
    role: LedgerRole = LedgerRole.MEMBER


class LedgerMemberRead(BaseModel):
    id: int
    ledger_id: int
    user_id: int
    email: str
    display_name: str
    role: LedgerRole
    created_at: datetime


class EntryBase(BaseModel):
    type: EntryType
    amount: Decimal = Field(gt=0)
    category: str = Field(min_length=1, max_length=80)
    subcategory: Optional[str] = Field(default=None, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    occurred_at: datetime


class EntryCreate(EntryBase):
    ledger_id: Optional[int] = None
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
    ledger_id: int
    raw_text: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: datetime


class ParsedEntry(EntryBase):
    confidence: float = Field(ge=0, le=1)


class ParsedTransaction(BaseModel):
    amount: Optional[Decimal] = Field(default=None, gt=0)
    category: Optional[str] = Field(default=None, max_length=80)
    occurred_at: Optional[datetime] = None
    type: Optional[EntryType] = None
    confidence: float = Field(ge=0, le=1)
    follow_up_fields: list[Literal["amount", "category", "occurred_at", "type"]] = Field(default_factory=list)
    follow_up_question: Optional[str] = Field(default=None, max_length=300)
    description: Optional[str] = Field(default=None, max_length=500)
    subcategory: Optional[str] = Field(default=None, max_length=80)

    @property
    def is_complete(self) -> bool:
        return all((self.amount, self.category, self.occurred_at, self.type)) and not self.follow_up_fields


class ChatRecordRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    pending_context: Optional[ParsedTransaction] = None


class AssistantPersonaBase(BaseModel):
    assistant_name: str = Field(default="账小喵", min_length=1, max_length=40)
    avatar: str = Field(default="🐱", min_length=1, max_length=500)
    voice_style: VoiceStyle = VoiceStyle.WARM
    mode: PersonaMode = PersonaMode.CUTE
    reply_length: Literal["short", "medium", "detailed"] = "short"
    emoji_level: int = Field(default=1, ge=0, le=3)
    proactive_insights: bool = True
    custom_instructions: str = Field(default="", max_length=500)


class AssistantPersonaUpdate(AssistantPersonaBase):
    pass


class AssistantPersonaRead(AssistantPersonaBase):
    user_id: int
    created_at: datetime
    updated_at: datetime


class ChatRecordResponse(BaseModel):
    assistant_name: str = "账小喵"
    assistant_avatar: str = "🐱"
    reply: str
    entry: Optional[EntryRead] = None
    parsed: ParsedTransaction
    needs_follow_up: bool = False


class ChatMessageRead(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    parsed: Optional[ParsedTransaction] = None
    recorded: bool = False
    created_at: datetime


class AvatarUploadResponse(BaseModel):
    url: str


class BudgetCreate(BaseModel):
    ledger_id: Optional[int] = None
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


class DailyCashFlow(BaseModel):
    date: date
    expense: Decimal
    income: Decimal


class SpecialFlowSummary(BaseModel):
    amount: Decimal
    count: int


class AnalysisInsight(BaseModel):
    headline: str = Field(max_length=120)
    summary: str = Field(max_length=600)
    highlights: list[str] = Field(default_factory=list, max_length=5)
    suggestions: list[str] = Field(default_factory=list, max_length=5)


class PeriodAnalysis(BaseModel):
    start_date: date
    end_date: date
    days: int
    entry_count: int
    expense_total: Decimal
    income_total: Decimal
    balance: Decimal
    consumption_total: Decimal
    ordinary_income_total: Decimal
    average_daily_consumption: Decimal
    borrowed: SpecialFlowSummary
    repayment_received: SpecialFlowSummary
    lent_out: SpecialFlowSummary
    repayment_paid: SpecialFlowSummary
    categories: list[CategorySummary]
    daily: list[DailyCashFlow]
    insight: AnalysisInsight
    ai_used: bool = False
    ai_warning: Optional[str] = None


class PreferenceCreate(BaseModel):
    keyword: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    subcategory: Optional[str] = None


class PreferenceRead(PreferenceCreate):
    id: int
    hit_count: int


class LoanBase(BaseModel):
    creditor: str = Field(min_length=1, max_length=120)
    borrowed_at: date
    principal: Decimal = Field(gt=0)
    repayment_months: int = Field(gt=0, le=600)
    annual_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    repayment_method: Literal["equal_payment", "equal_principal"] = "equal_payment"
    first_payment_date: date
    note: str = Field(default="", max_length=500)


class LoanCreate(LoanBase):
    ledger_id: Optional[int] = None


class LoanUpdate(BaseModel):
    creditor: Optional[str] = Field(default=None, min_length=1, max_length=120)
    borrowed_at: Optional[date] = None
    principal: Optional[Decimal] = Field(default=None, gt=0)
    repayment_months: Optional[int] = Field(default=None, gt=0, le=600)
    annual_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    repayment_method: Optional[Literal["equal_payment", "equal_principal"]] = None
    first_payment_date: Optional[date] = None
    note: Optional[str] = Field(default=None, max_length=500)


class LoanRead(LoanBase):
    id: int
    ledger_id: int
    created_at: datetime
    updated_at: datetime
