import { Bot, SendHorizontal } from "lucide-react";
import { FormEvent, useState } from "react";
import { apiClient } from "../services/apiClient";
import type { AssistantTone, Entry } from "../types";
interface Props { assistantTone: AssistantTone; onEntryCreated: (entry: Entry) => void; }
interface Message { role: "user" | "assistant"; content: string; }
export function ChatPage({ assistantTone, onEntryCreated }: Props) {
  const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false); const [messages, setMessages] = useState<Message[]>([{ role: "assistant", content: "你好，我是账小喵。告诉我花了多少钱，剩下的交给我。" }]);
  async function submit(event: FormEvent) { event.preventDefault(); const text = message.trim(); if (!text || busy) return; setMessage(""); setBusy(true); setMessages((m) => [...m, { role: "user", content: text }]); try { const result = await apiClient.recordFromChat(text, assistantTone); onEntryCreated(result.entry); setMessages((m) => [...m, { role: "assistant", content: result.reply }]); } catch (err) { setMessages((m) => [...m, { role: "assistant", content: err instanceof Error ? err.message : "记账失败，请稍后再试。" }]); } finally { setBusy(false); } }
  return <section className="work-area"><header className="page-header"><div><p className="eyebrow">AI 记账助手</p><h1>说一句话，账单就记好了</h1><p className="subtle">例如：今天午饭 22 元，或者收到工资 8000 元。</p></div><div className="assistant-chip"><Bot size={17} />账小喵在线</div></header><div className="chat-panel"><div className="message-list">{messages.map((item, index) => <div key={`${item.role}-${index}`} className={`message ${item.role}`}>{item.content}</div>)}{busy && <div className="message assistant typing">正在整理这笔账...</div>}</div><form className="composer" onSubmit={submit}><input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="输入消费或收入，例如：打车 23 元" /><button type="submit" disabled={busy || !message.trim()} title="发送"><SendHorizontal size={18} /></button></form></div></section>;
}
