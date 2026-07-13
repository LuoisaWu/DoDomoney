import { SendHorizontal } from "lucide-react";
import { FormEvent, useState } from "react";

import { apiClient } from "../services/apiClient";
import type { AssistantTone, Entry } from "../types";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatPageProps {
  assistantTone: AssistantTone;
  onEntryCreated: (entry: Entry) => void;
}

export function ChatPage({ assistantTone, onEntryCreated }: ChatPageProps) {
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "我是账小喵。直接告诉我你花了多少钱，或者收入了多少钱。"
    }
  ]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const text = message.trim();
    if (!text || isSubmitting) return;

    setMessage("");
    setIsSubmitting(true);
    setMessages((current) => [...current, { role: "user", content: text }]);

    try {
      const result = await apiClient.recordFromChat(text, assistantTone);
      onEntryCreated(result.entry);
      setMessages((current) => [...current, { role: "assistant", content: result.reply }]);
    } catch (err) {
      const content = err instanceof Error ? err.message : "记账失败，请稍后再试。";
      setMessages((current) => [...current, { role: "assistant", content }]);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="work-area">
      <header className="page-header">
        <div>
          <p className="eyebrow">AI 记账助手</p>
          <h1>和账小喵说一句话就能记账</h1>
        </div>
      </header>

      <div className="chat-panel">
        <div className="message-list">
          {messages.map((item, index) => (
            <div key={`${item.role}-${index}`} className={`message ${item.role}`}>
              {item.content}
            </div>
          ))}
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="例如：今天午饭 22 元"
          />
          <button type="submit" disabled={isSubmitting} title="发送">
            <SendHorizontal size={18} />
          </button>
        </form>
      </div>
    </section>
  );
}
