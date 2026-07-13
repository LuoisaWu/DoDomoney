export type EntryType = "expense" | "income";
export type AssistantTone = "cute" | "snarky" | "gentle" | "advisor" | "minimal";

export interface Entry {
  id: number; type: EntryType; amount: string; category: string; subcategory?: string | null;
  description: string; occurred_at: string; raw_text?: string | null; source: string;
  created_at: string; updated_at: string;
}
export interface ParsedEntry { type: EntryType; amount: string; category: string; subcategory?: string | null; description: string; occurred_at: string; confidence: number; }
export interface ChatRecordResponse { assistant_name: string; reply: string; entry: Entry; parsed: ParsedEntry; }
export interface Budget { id: number; month: string; amount: string; category?: string | null; created_at: string; }
export interface CategorySummary { category: string; amount: string; percentage: number; }
export interface MonthlySummary { month: string; expense_total: string; income_total: string; balance: string; entry_count: number; categories: CategorySummary[]; }
