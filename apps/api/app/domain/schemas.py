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
    verification_code: str = Field(pattern=r"^\d{6}$")


class VerificationCodeRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class VerificationCodeResponse(BaseModel):
    message: str
    retry_after: int
    expires_in: int
    development_code: Optional[str] = None


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
    target_ledger_id: Optional[int] = None
    target_ledger_name: Optional[str] = Field(default=None, max_length=120)

    @property
    def is_complete(self) -> bool:
        return all((self.amount, self.category, self.occurred_at, self.type)) and not self.follow_up_fields


LoanFollowUpField = Literal[
    "creditor",
    "borrowed_at",
    "principal",
    "repayment_months",
    "annual_rate",
    "repayment_method",
    "first_payment_date",
]


class ParsedLoan(BaseModel):
    creditor: Optional[str] = Field(default=None, max_length=120)
    borrowed_at: Optional[date] = None
    principal: Optional[Decimal] = Field(default=None, gt=0)
    repayment_months: Optional[int] = Field(default=None, gt=0, le=600)
    annual_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    repayment_method: Optional[Literal["equal_payment", "equal_principal"]] = None
    first_payment_date: Optional[date] = None
    note: str = Field(default="", max_length=500)
    confidence: float = Field(default=0.8, ge=0, le=1)
    follow_up_fields: list[LoanFollowUpField] = Field(default_factory=list)
    follow_up_question: Optional[str] = Field(default=None, max_length=300)
    awaiting_confirmation: bool = False
    target_ledger_id: Optional[int] = None
    target_ledger_name: Optional[str] = Field(default=None, max_length=120)

    @property
    def is_complete(self) -> bool:
        required = (
            self.creditor,
            self.borrowed_at,
            self.principal,
            self.repayment_months,
            self.annual_rate is not None,
            self.repayment_method,
            self.first_payment_date,
        )
        return all(required) and not self.follow_up_fields


ReimbursementFollowUpField = Literal["merchant", "amount", "invoice_date", "category"]


class ParsedReimbursement(BaseModel):
    merchant: Optional[str] = Field(default=None, max_length=120)
    invoice_title: str = Field(default="", max_length=120)
    amount: Optional[Decimal] = Field(default=None, gt=0)
    invoice_date: Optional[date] = None
    category: Optional[str] = Field(default=None, max_length=80)
    invoice_number: str = Field(default="", max_length=80)
    status: Literal["pending", "submitted", "reimbursed"] = "pending"
    note: str = Field(default="", max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=1000)
    confidence: float = Field(default=0.8, ge=0, le=1)
    follow_up_fields: list[ReimbursementFollowUpField] = Field(default_factory=list)
    follow_up_question: Optional[str] = Field(default=None, max_length=300)
    awaiting_confirmation: bool = False
    target_ledger_id: Optional[int] = None
    target_ledger_name: Optional[str] = Field(default=None, max_length=120)

    @property
    def is_complete(self) -> bool:
        return all((self.merchant, self.amount, self.invoice_date, self.category)) and not self.follow_up_fields


class DocumentOcrContext(BaseModel):
    image_url: str = Field(max_length=1000)
    extracted_text: str = Field(default="", max_length=10000)
    document_type: Literal["invoice", "loan_note", "repayment", "unknown"] = "unknown"
    confidence: float = Field(default=0, ge=0, le=1)
    status: Literal["completed", "pending_provider"] = "pending_provider"


class ChatRecordRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    pending_context: Optional[ParsedTransaction] = None
    pending_loan: Optional[ParsedLoan] = None
    pending_reimbursement: Optional[ParsedReimbursement] = None
    image_context: Optional[DocumentOcrContext] = None


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
    loan_id: Optional[int] = None
    reimbursement_id: Optional[int] = None
    record_type: Literal["transaction", "loan", "reimbursement"] = "transaction"
    parsed: Optional[ParsedTransaction] = None
    parsed_loan: Optional[ParsedLoan] = None
    parsed_reimbursement: Optional[ParsedReimbursement] = None
    needs_follow_up: bool = False


class ChatMessageRead(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    parsed: Optional[ParsedTransaction] = None
    parsed_loan: Optional[ParsedLoan] = None
    parsed_reimbursement: Optional[ParsedReimbursement] = None
    image_url: Optional[str] = None
    recorded: bool = False
    created_at: datetime


class AvatarUploadResponse(BaseModel):
    url: str


class DocumentOcrResponse(DocumentOcrContext):
    provider_configured: bool = False
    message: str


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


class ReimbursementBase(BaseModel):
    merchant: str = Field(min_length=1, max_length=120)
    invoice_title: str = Field(default="", max_length=120)
    amount: Decimal = Field(gt=0)
    invoice_date: date
    category: str = Field(min_length=1, max_length=80)
    invoice_number: str = Field(default="", max_length=80)
    status: Literal["pending", "submitted", "reimbursed"] = "pending"
    note: str = Field(default="", max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=1000)


class ReimbursementCreate(ReimbursementBase):
    ledger_id: Optional[int] = None


class ReimbursementUpdate(BaseModel):
    merchant: Optional[str] = Field(default=None, min_length=1, max_length=120)
    invoice_title: Optional[str] = Field(default=None, max_length=120)
    amount: Optional[Decimal] = Field(default=None, gt=0)
    invoice_date: Optional[date] = None
    category: Optional[str] = Field(default=None, min_length=1, max_length=80)
    invoice_number: Optional[str] = Field(default=None, max_length=80)
    status: Optional[Literal["pending", "submitted", "reimbursed"]] = None
    note: Optional[str] = Field(default=None, max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=1000)


class ReimbursementRead(ReimbursementBase):
    id: int
    ledger_id: int
    created_at: datetime
    updated_at: datetime
