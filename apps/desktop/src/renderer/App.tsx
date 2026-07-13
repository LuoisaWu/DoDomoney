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
  { key: "chat", label: "AI 记账", icon: Bot }, { key: "entries", label: "账单明细", icon: ClipboardList },
  { key: "insights", label: "数据统计", icon: BarChart3 }, { key: "settings", label: "助手设置", icon: Settings }
];
export function App() {
  const [page, setPage] = useState<Page>("chat"); const [entries, setEntries] = useState<Entry[]>([]);
  const [assistantTone, setAssistantTone] = useState<AssistantTone>(() => (localStorage.getItem("assistant-tone") as AssistantTone) || "cute"); const [error, setError] = useState<string | null>(null);
  async function refreshEntries() { try { setEntries(await apiClient.listEntries()); setError(null); } catch (err) { setError(err instanceof Error ? err.message : "无法连接后端服务"); } }
  useEffect(() => { void refreshEntries(); }, []);
  function changeTone(tone: AssistantTone) { setAssistantTone(tone); localStorage.setItem("assistant-tone", tone); }
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-mark"><WalletCards size={22} /></div><div><strong>Dodomoney</strong><span>钱多多 · AI 财务助手</span></div></div><nav className="nav-list">{navItems.map(({ key, label, icon: Icon }) => <button key={key} className={page === key ? "nav-item active" : "nav-item"} onClick={() => setPage(key)} title={label}><Icon size={18} /><span>{label}</span></button>)}</nav><div className="sidebar-note"><strong>今日小目标</strong><span>记下每一笔，月底更从容。</span></div></aside><main className="main-panel">{error && <div className="status-banner">{error}</div>}{page === "chat" && <ChatPage assistantTone={assistantTone} onEntryCreated={(entry) => setEntries((current) => [entry, ...current])} />}{page === "entries" && <EntriesPage entries={entries} onRefresh={refreshEntries} onDelete={async (id) => { await apiClient.deleteEntry(id); await refreshEntries(); }} />}{page === "insights" && <InsightsPage entries={entries} />}{page === "settings" && <SettingsPage assistantTone={assistantTone} onToneChange={changeTone} />}</main></div>;
}
