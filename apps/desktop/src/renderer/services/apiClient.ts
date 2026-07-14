import type { AssistantPersona, Budget, ChatMessage, ChatRecordResponse, Entry, EntryUpdate, Ledger, LedgerMember, LedgerType, Loan, LoanCreate, LoginResponse, MonthlySummary, ParsedTransaction, PeriodAnalysis, User } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
let context: { userId?: number; ledgerId?: number; token?: string } = {};

export function setApiContext(next: { userId?: number; ledgerId?: number; token?: string }) { context = next; }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { ...(init?.headers as Record<string, string> | undefined) };
  if (!(init?.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (context.userId) headers["X-Dodomoney-User-Id"] = String(context.userId);
  if (context.ledgerId) headers["X-Dodomoney-Ledger-Id"] = String(context.ledgerId);
  if (context.token) headers.Authorization = `Bearer ${context.token}`;
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail ?? `Request failed (${response.status})`); }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const apiClient = {
  login: (email: string, password: string) => request<LoginResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (email: string, displayName: string, password: string) => request<LoginResponse>("/auth/register", { method: "POST", body: JSON.stringify({ email, display_name: displayName, password }) }),
  restoreSession: () => request<LoginResponse>("/auth/session"),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  listUsers: () => request<User[]>("/users"),
  updateCurrentUser: (payload: { display_name?: string; avatar_url?: string }) => request<User>("/users/me", { method: "PATCH", body: JSON.stringify(payload) }),
  listLedgers: () => request<Ledger[]>("/ledgers"),
  createLedger: (name: string, type: LedgerType) => request<Ledger>("/ledgers", { method: "POST", body: JSON.stringify({ name, type }) }),
  listMembers: (ledgerId: number) => request<LedgerMember[]>(`/ledgers/${ledgerId}/members`),
  addMember: (ledgerId: number, email: string, displayName?: string, role = "member") => request<LedgerMember>(`/ledgers/${ledgerId}/members`, { method: "POST", body: JSON.stringify({ email, display_name: displayName || null, role }) }),
  listEntries: () => request<Entry[]>("/entries"),
  updateEntry: (id: number, payload: EntryUpdate) => request<Entry>(`/entries/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteEntry: (id: number) => request<void>(`/entries/${id}`, { method: "DELETE" }),
  recordFromChat: (message: string, pendingContext?: ParsedTransaction | null) => request<ChatRecordResponse>("/chat/record", { method: "POST", body: JSON.stringify({ message, pending_context: pendingContext || null }) }),
  listChatMessages: () => request<ChatMessage[]>("/chat/messages"),
  clearChatMessages: () => request<void>("/chat/messages", { method: "DELETE" }),
  uploadAvatar: (file: File) => { const body = new FormData(); body.append("file", file); return request<{ url: string }>("/uploads/avatar", { method: "POST", body }); },
  getPersona: () => request<AssistantPersona>("/users/me/persona"),
  updatePersona: (persona: Pick<AssistantPersona, "assistant_name" | "avatar" | "voice_style" | "mode" | "reply_length" | "emoji_level" | "proactive_insights" | "custom_instructions">) => request<AssistantPersona>("/users/me/persona", { method: "PUT", body: JSON.stringify(persona) }),
  summary: (month: string) => request<MonthlySummary>(`/entries/summary?month=${month}`),
  analyze: (startDate: string, endDate: string, includeAi = false) => request<PeriodAnalysis>(`/entries/analysis?start_date=${startDate}&end_date=${endDate}&include_ai=${includeAi}`),
  listBudgets: () => request<Budget[]>("/budgets"),
  createBudget: (month: string, amount: string, category?: string) => request<Budget>("/budgets", { method: "POST", body: JSON.stringify({ month: `${month}-01`, amount, category: category || null }) }),
  deleteBudget: (id: number) => request<void>(`/budgets/${id}`, { method: "DELETE" }),
  listLoans: () => request<Loan[]>("/loans"),
  createLoan: (payload: LoanCreate) => request<Loan>("/loans", { method: "POST", body: JSON.stringify(payload) }),
  updateLoan: (id: number, payload: Partial<LoanCreate>) => request<Loan>(`/loans/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteLoan: (id: number) => request<void>(`/loans/${id}`, { method: "DELETE" })
};
