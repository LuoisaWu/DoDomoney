import type { AssistantTone, Budget, ChatRecordResponse, Entry, MonthlySummary } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { headers: { "Content-Type": "application/json", ...init?.headers }, ...init });
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail ?? `请求失败（${response.status}）`); }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export const apiClient = {
  listEntries: () => request<Entry[]>("/entries"),
  deleteEntry: (id: number) => request<void>(`/entries/${id}`, { method: "DELETE" }),
  recordFromChat: (message: string, assistantTone: AssistantTone) => request<ChatRecordResponse>("/chat/record", { method: "POST", body: JSON.stringify({ message, assistant_tone: assistantTone }) }),
  summary: (month: string) => request<MonthlySummary>(`/entries/summary?month=${month}`),
  listBudgets: () => request<Budget[]>("/budgets"),
  createBudget: (month: string, amount: string, category?: string) => request<Budget>("/budgets", { method: "POST", body: JSON.stringify({ month: `${month}-01`, amount, category: category || null }) }),
  deleteBudget: (id: number) => request<void>(`/budgets/${id}`, { method: "DELETE" })
};
