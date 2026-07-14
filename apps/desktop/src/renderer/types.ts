export type EntryType = "expense" | "income";
export type PersonaMode = "balanced" | "cute" | "rational" | "encouraging" | "witty_dark";
export type VoiceStyle = "warm" | "playful" | "direct" | "calm";
export type ReplyLength = "short" | "medium" | "detailed";
export type LedgerType = "personal" | "family" | "shared";
export type LedgerRole = "owner" | "admin" | "member";

export interface User {
  id: number; email: string; display_name: string; avatar_url?: string | null;
  created_at: string; updated_at: string;
}
export interface Ledger {
  id: number; owner_user_id: number; name: string; type: LedgerType; role: LedgerRole;
  member_count: number; created_at: string; updated_at: string;
}
export interface LedgerMember {
  id: number; ledger_id: number; user_id: number; email: string; display_name: string;
  role: LedgerRole; created_at: string;
}
export interface LoginResponse { user: User; ledgers: Ledger[]; active_ledger_id: number; token: string; }

export interface Entry {
  id: number; ledger_id: number; type: EntryType; amount: string; category: string; subcategory?: string | null;
  description: string; occurred_at: string; raw_text?: string | null; source: string;
  created_at: string; updated_at: string;
}
export interface EntryUpdate {
  amount?: string; category?: string; description?: string; occurred_at?: string;
}
export interface ParsedTransaction {
  type?: EntryType | null; amount?: string | null; category?: string | null; subcategory?: string | null;
  description?: string | null; occurred_at?: string | null; confidence: number;
  follow_up_fields: Array<"amount" | "category" | "occurred_at" | "type">;
  follow_up_question?: string | null;
}
export type LoanFollowUpField = "creditor" | "borrowed_at" | "principal" | "repayment_months" | "annual_rate" | "repayment_method" | "first_payment_date";
export interface ParsedLoan extends LoanDraft {
  confidence: number; follow_up_fields: LoanFollowUpField[]; follow_up_question?: string | null; awaiting_confirmation: boolean;
}
export interface AssistantPersona {
  user_id: number; assistant_name: string; avatar: string; voice_style: VoiceStyle;
  mode: PersonaMode; reply_length: ReplyLength; emoji_level: number;
  proactive_insights: boolean; custom_instructions: string; created_at: string; updated_at: string;
}
export interface ChatRecordResponse {
  assistant_name: string; assistant_avatar: string; reply: string; entry?: Entry | null; loan_id?: number | null;
  record_type: "transaction" | "loan"; parsed?: ParsedTransaction | null; parsed_loan?: ParsedLoan | null; needs_follow_up: boolean;
}
export interface ChatMessage { id: number; role: "user" | "assistant"; content: string; parsed?: ParsedTransaction | null; parsed_loan?: ParsedLoan | null; recorded: boolean; created_at: string; }
export interface Budget { id: number; ledger_id: number; month: string; amount: string; category?: string | null; created_at: string; }
export interface CategorySummary { category: string; amount: string; percentage: number; }
export interface MonthlySummary { month: string; expense_total: string; income_total: string; balance: string; entry_count: number; categories: CategorySummary[]; }
export interface DailyCashFlow { date: string; expense: string; income: string; }
export interface SpecialFlowSummary { amount: string; count: number; }
export interface AnalysisInsight { headline: string; summary: string; highlights: string[]; suggestions: string[]; }
export interface PeriodAnalysis {
  start_date: string; end_date: string; days: number; entry_count: number;
  expense_total: string; income_total: string; balance: string;
  consumption_total: string; ordinary_income_total: string; average_daily_consumption: string;
  borrowed: SpecialFlowSummary; repayment_received: SpecialFlowSummary;
  lent_out: SpecialFlowSummary; repayment_paid: SpecialFlowSummary;
  categories: CategorySummary[]; daily: DailyCashFlow[]; insight: AnalysisInsight;
  ai_used: boolean; ai_warning?: string | null;
}
export type RepaymentMethod = "equal_payment" | "equal_principal";
export interface Loan {
  id: number; ledger_id: number; creditor: string; borrowed_at: string; principal: string;
  repayment_months: number; annual_rate: string; repayment_method: RepaymentMethod;
  first_payment_date: string; note: string; created_at: string; updated_at: string;
}
export interface LoanDraft {
  creditor?: string; borrowed_at?: string; principal?: string; repayment_months?: number;
  annual_rate?: string; repayment_method?: RepaymentMethod; first_payment_date?: string; note?: string;
}
export type LoanCreate = Required<Omit<LoanDraft, "note">> & { note: string };
