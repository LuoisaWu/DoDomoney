import type { Entry } from "../types";

interface InsightsPageProps {
  entries: Entry[];
}

export function InsightsPage({ entries }: InsightsPageProps) {
  const expenseTotal = entries
    .filter((entry) => entry.type === "expense")
    .reduce((sum, entry) => sum + Number(entry.amount), 0);
  const incomeTotal = entries
    .filter((entry) => entry.type === "income")
    .reduce((sum, entry) => sum + Number(entry.amount), 0);

  return (
    <section className="work-area">
      <header className="page-header">
        <div>
          <p className="eyebrow">消费统计</p>
          <h1>本阶段概览</h1>
        </div>
      </header>

      <div className="metric-grid">
        <div className="metric-card">
          <span>总支出</span>
          <strong>{expenseTotal.toFixed(2)}</strong>
        </div>
        <div className="metric-card">
          <span>总收入</span>
          <strong>{incomeTotal.toFixed(2)}</strong>
        </div>
        <div className="metric-card">
          <span>结余</span>
          <strong>{(incomeTotal - expenseTotal).toFixed(2)}</strong>
        </div>
      </div>
    </section>
  );
}
