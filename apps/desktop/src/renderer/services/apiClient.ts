import type { AssistantTone, Budget, ChatRecordResponse, Entry } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  listEntries() {
    return request<Entry[]>("/entries");
  },
  recordFromChat(message: string, assistantTone: AssistantTone) {
    return request<ChatRecordResponse>("/chat/record", {
      method: "POST",
      body: JSON.stringify({ message, assistant_tone: assistantTone })
    });
  },
  listBudgets() {
    return request<Budget[]>("/budgets");
  }
};
