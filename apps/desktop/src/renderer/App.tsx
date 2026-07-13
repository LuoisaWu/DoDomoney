import { BarChart3, Bot, ClipboardList, Settings, WalletCards } from "lucide-react";
import { useEffect, useState } from "react";

import { ChatPage } from "./pages/ChatPage";
import { EntriesPage } from "./pages/EntriesPage";
import { InsightsPage } from "./pages/InsightsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { apiClient } from "./services/apiClient";
import type { AssistantTone, Entry } from "./types";

type Page = "chat" | "entries" | "insights" | "settings";

const navItems: Array<{ key: Page; label: string; icon: typeof Bot }> = [
  { key: "chat", label: "记账", icon: Bot },
  { key: "entries", label: "明细", icon: ClipboardList },
  { key: "insights", label: "统计", icon: BarChart3 },
  { key: "settings", label: "设置", icon: Settings }
];

export function App() {
  const [page, setPage] = useState<Page>("chat");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [assistantTone, setAssistantTone] = useState<AssistantTone>("cute");
  const [error, setError] = useState<string | null>(null);

  async function refreshEntries() {
    try {
      setEntries(await apiClient.listEntries());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "无法连接后端服务");
    }
  }

  useEffect(() => {
    void refreshEntries();
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <WalletCards size={22} />
          </div>
          <div>
            <strong>Dodomoney</strong>
            <span>钱多多</span>
          </div>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={page === item.key ? "nav-item active" : "nav-item"}
                onClick={() => setPage(item.key)}
                title={item.label}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="main-panel">
        {error && <div className="status-banner">{error}</div>}
        {page === "chat" && (
          <ChatPage
            assistantTone={assistantTone}
            onEntryCreated={(entry) => setEntries((current) => [entry, ...current])}
          />
        )}
        {page === "entries" && <EntriesPage entries={entries} onRefresh={refreshEntries} />}
        {page === "insights" && <InsightsPage entries={entries} />}
        {page === "settings" && (
          <SettingsPage assistantTone={assistantTone} onToneChange={setAssistantTone} />
        )}
      </main>
    </div>
  );
}
