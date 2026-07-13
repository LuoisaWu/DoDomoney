export type EntryType = "expense" | "income";
export type AssistantTone = "cute" | "snarky" | "gentle" | "advisor" | "minimal";

export interface Entry {
  id: number;
  type: EntryType;
  amount: string;
  category: string;
  subcategory?: string | null;
  description: string;
  occurred_at: string;
  raw_text?: string | null;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface ChatRecordResponse {
  assistant_name: string;
  reply: string;
  entry: Entry;
}

export interface Budget {
  id: number;
  month: string;
  amount: string;
  category?: string | null;
  created_at: string;
}
