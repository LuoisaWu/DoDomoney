import { RefreshCcw } from "lucide-react";

import type { Entry } from "../types";

interface EntriesPageProps {
  entries: Entry[];
  onRefresh: () => void;
}

export function EntriesPage({ entries, onRefresh }: EntriesPageProps) {
  return (
    <section className="work-area">
      <header className="page-header">
        <div>
          <p className="eyebrow">账单明细</p>
          <h1>最近记录</h1>
        </div>
        <button className="icon-button" onClick={onRefresh} title="刷新">
          <RefreshCcw size={18} />
        </button>
      </header>

      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th>时间</th>
              <th>类型</th>
              <th>分类</th>
              <th>描述</th>
              <th>金额</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.id}>
                <td>{new Date(entry.occurred_at).toLocaleString()}</td>
                <td>{entry.type === "expense" ? "支出" : "收入"}</td>
                <td>{entry.subcategory ? `${entry.category} / ${entry.subcategory}` : entry.category}</td>
                <td>{entry.description}</td>
                <td className={entry.type === "expense" ? "amount expense" : "amount income"}>
                  {entry.type === "expense" ? "-" : "+"}
                  {entry.amount}
                </td>
              </tr>
            ))}
            {entries.length === 0 && (
              <tr>
                <td colSpan={5} className="empty-cell">
                  暂无账单
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
