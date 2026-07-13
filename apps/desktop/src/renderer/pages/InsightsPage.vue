<script setup lang="ts">
import { CalendarDays, Plus, Sparkles, Trash2, TrendingDown, TrendingUp, WalletCards } from "lucide-vue-next";
import { computed, onMounted, ref, watch } from "vue";
import { apiClient } from "../services/apiClient";
import type { Budget, Entry, PeriodAnalysis } from "../types";

const props = defineProps<{ entries: Entry[] }>();
type Preset = "week" | "month" | "7days" | "30days" | "custom";

function localDate(value = new Date()) {
  const offset = value.getTimezoneOffset() * 60_000;
  return new Date(value.getTime() - offset).toISOString().slice(0, 10);
}

function presetRange(preset: Preset) {
  const today = new Date();
  const start = new Date(today);
  if (preset === "week") {
    const weekday = today.getDay() || 7;
    start.setDate(today.getDate() - weekday + 1);
  } else if (preset === "month") start.setDate(1);
  else if (preset === "7days") start.setDate(today.getDate() - 6);
  else if (preset === "30days") start.setDate(today.getDate() - 29);
  return { start: localDate(start), end: localDate(today) };
}

const initialRange = presetRange("week");
const preset = ref<Preset>("week");
const startDate = ref(initialRange.start);
const endDate = ref(initialRange.end);
const analysis = ref<PeriodAnalysis | null>(null);
const budgets = ref<Budget[]>([]);
const budgetAmount = ref("");
const loading = ref(false);
const aiLoading = ref(false);
const error = ref("");
const requestId = ref(0);

const periodLabel = computed(() => analysis.value ? `${analysis.value.start_date} 至 ${analysis.value.end_date} · ${analysis.value.days} 天` : "");
const budgetMonth = computed(() => startDate.value.slice(0, 7));
const maxDaily = computed(() => Math.max(1, ...(analysis.value?.daily.flatMap((item) => [Number(item.expense), Number(item.income)]) ?? [1])));

function money(value?: string) {
  return Number(value ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function shortDate(value: string) { return `${Number(value.slice(5, 7))}/${Number(value.slice(8, 10))}`; }

function choosePreset(next: Preset) {
  preset.value = next;
  if (next !== "custom") {
    const range = presetRange(next);
    startDate.value = range.start;
    endDate.value = range.end;
  }
}

async function loadAnalysis(includeAi = false) {
  if (!startDate.value || !endDate.value || startDate.value > endDate.value) {
    error.value = "请选择有效的开始和结束日期。";
    return;
  }
  const currentRequest = ++requestId.value;
  if (includeAi) aiLoading.value = true; else loading.value = true;
  error.value = "";
  try {
    const result = await apiClient.analyze(startDate.value, endDate.value, includeAi);
    if (currentRequest === requestId.value) analysis.value = result;
  } catch (err) {
    if (currentRequest === requestId.value) error.value = err instanceof Error ? err.message : "分析加载失败";
  } finally {
    if (currentRequest === requestId.value) { loading.value = false; aiLoading.value = false; }
  }
}

async function loadBudgets() {
  try {
    const list = await apiClient.listBudgets();
    budgets.value = list.filter((item) => item.month.startsWith(budgetMonth.value));
  } catch { budgets.value = []; }
}
async function addBudget() {
  if (!budgetAmount.value) return;
  await apiClient.createBudget(budgetMonth.value, budgetAmount.value);
  budgetAmount.value = "";
  await loadBudgets();
}
async function deleteBudget(id: number) {
  await apiClient.deleteBudget(id);
  budgets.value = budgets.value.filter((item) => item.id !== id);
}

watch([startDate, endDate], () => { void loadAnalysis(); void loadBudgets(); });
watch(() => props.entries.length, () => void loadAnalysis());
onMounted(() => { void loadAnalysis(); void loadBudgets(); });
</script>

<template>
  <section class="work-area analysis-page">
    <header class="page-header analysis-header">
      <div>
        <p class="eyebrow">收支分析</p>
        <h1>看清每一段时间里的资金变化</h1>
        <p class="subtle">消费、收入、借入和他人还款分开统计，避免把借来的钱误当成收入。</p>
      </div>
      <button class="ai-button" :disabled="aiLoading || loading || !analysis?.entry_count" @click="loadAnalysis(true)">
        <Sparkles :size="17" />{{ aiLoading ? "AI 分析中…" : "AI 智能解读" }}
      </button>
    </header>

    <div class="analysis-toolbar">
      <div class="preset-tabs">
        <button v-for="item in ([['week', '本周'], ['month', '本月'], ['7days', '近 7 天'], ['30days', '近 30 天'], ['custom', '自定义']] as const)" :key="item[0]" :class="{ active: preset === item[0] }" @click="choosePreset(item[0])">{{ item[1] }}</button>
      </div>
      <div class="date-range">
        <CalendarDays :size="16" /><input v-model="startDate" type="date" @focus="preset = 'custom'" /><span>至</span><input v-model="endDate" type="date" @focus="preset = 'custom'" />
      </div>
    </div>

    <div v-if="error" class="status-banner">{{ error }}</div>
    <div v-if="loading" class="loading-line">正在汇总 {{ startDate }} 至 {{ endDate }} 的账单…</div>

    <template v-if="analysis">
      <div class="analysis-meta">{{ periodLabel }} · 共 {{ analysis.entry_count }} 笔账单</div>
      <div class="metric-grid analysis-metrics">
        <div class="metric-card expense-card"><span>消费支出</span><strong>¥ {{ money(analysis.consumption_total) }}</strong><small>日均 ¥ {{ money(analysis.average_daily_consumption) }}</small></div>
        <div class="metric-card income-card"><span>普通收入</span><strong>¥ {{ money(analysis.ordinary_income_total) }}</strong><small>不含借款和收回款</small></div>
        <div class="metric-card"><span>全部现金流结余</span><strong :class="Number(analysis.balance) >= 0 ? 'positive' : 'negative'">¥ {{ money(analysis.balance) }}</strong><small>全部流入减全部流出</small></div>
        <div class="metric-card special-card"><span>借钱收到</span><strong>¥ {{ money(analysis.borrowed.amount) }}</strong><small>{{ analysis.borrowed.count }} 笔借入</small></div>
        <div class="metric-card special-card"><span>收到别人还款</span><strong>¥ {{ money(analysis.repayment_received.amount) }}</strong><small>{{ analysis.repayment_received.count }} 笔收回款</small></div>
      </div>

      <div class="ai-insight-card">
        <div class="insight-icon"><Sparkles :size="20" /></div>
        <div>
          <div class="ai-insight-title"><span>{{ analysis.ai_used ? "AI 解读" : "智能摘要" }}</span><em v-if="analysis.ai_used">仅发送匿名汇总数据</em></div>
          <h2>{{ analysis.insight.headline }}</h2><p>{{ analysis.insight.summary }}</p>
          <div class="insight-columns">
            <ul v-if="analysis.insight.highlights.length"><li v-for="item in analysis.insight.highlights" :key="item"><TrendingUp :size="15" />{{ item }}</li></ul>
            <ul v-if="analysis.insight.suggestions.length"><li v-for="item in analysis.insight.suggestions" :key="item"><Sparkles :size="15" />{{ item }}</li></ul>
          </div>
          <small v-if="analysis.ai_warning" class="ai-warning">{{ analysis.ai_warning }}</small>
        </div>
      </div>

      <div class="analysis-grid">
        <div class="section-block">
          <div class="section-heading"><div><h2>消费分类</h2><span>借出和还款不计入消费</span></div></div>
          <template v-if="analysis.categories.length">
            <div v-for="item in analysis.categories" :key="item.category" class="category-row"><div><span>{{ item.category }}</span><strong>¥ {{ money(item.amount) }}</strong></div><div class="progress"><i :style="{ width: `${item.percentage}%` }" /></div><small>{{ item.percentage }}%</small></div>
          </template>
          <p v-else class="empty-copy">该时段没有消费记录。</p>
        </div>
        <div class="section-block flow-section">
          <div class="section-heading"><div><h2>借款与还款</h2><span>单独呈现，不混入日常收支</span></div></div>
          <div class="flow-row"><span><TrendingUp :size="17" />借入款</span><strong>+ ¥ {{ money(analysis.borrowed.amount) }}</strong><small>{{ analysis.borrowed.count }} 笔</small></div>
          <div class="flow-row"><span><WalletCards :size="17" />收到他人还款</span><strong>+ ¥ {{ money(analysis.repayment_received.amount) }}</strong><small>{{ analysis.repayment_received.count }} 笔</small></div>
          <div class="flow-row out"><span><TrendingDown :size="17" />借给别人</span><strong>- ¥ {{ money(analysis.lent_out.amount) }}</strong><small>{{ analysis.lent_out.count }} 笔</small></div>
          <div class="flow-row out"><span><TrendingDown :size="17" />偿还借款</span><strong>- ¥ {{ money(analysis.repayment_paid.amount) }}</strong><small>{{ analysis.repayment_paid.count }} 笔</small></div>
        </div>
      </div>

      <div class="section-block trend-section">
        <div class="section-heading"><div><h2>每日收支趋势</h2><span>绿色为收入，橙色为支出</span></div></div>
        <div class="trend-scroll"><div class="trend-chart" :style="{ minWidth: `${Math.max(analysis.daily.length * 42, 620)}px` }">
          <div v-for="day in analysis.daily" :key="day.date" class="trend-day" :title="`${day.date} 收入 ¥${money(day.income)} / 支出 ¥${money(day.expense)}`"><div class="trend-bars"><i class="income-bar" :style="{ height: `${Math.max(Number(day.income) / maxDaily * 100, Number(day.income) ? 3 : 0)}%` }" /><i class="expense-bar" :style="{ height: `${Math.max(Number(day.expense) / maxDaily * 100, Number(day.expense) ? 3 : 0)}%` }" /></div><small>{{ shortDate(day.date) }}</small></div>
        </div></div>
      </div>

      <div class="section-block budget-section">
        <div class="section-heading"><div><h2>{{ budgetMonth }} 月预算</h2><span>为所选区间所在月份设置消费边界</span></div></div>
        <div class="budget-add"><input v-model="budgetAmount" type="number" min="1" placeholder="预算金额" /><button class="primary-button" @click="addBudget"><Plus :size="16" />添加</button></div>
        <div v-for="budget in budgets" :key="budget.id" class="budget-row"><div><strong>{{ budget.category || "总预算" }}</strong><span>¥ {{ money(budget.amount) }}</span></div><button class="table-action" title="删除" @click="deleteBudget(budget.id)"><Trash2 :size="16" /></button></div>
        <p v-if="!budgets.length" class="empty-copy">这个月还没有设置预算。</p>
      </div>
    </template>
  </section>
</template>
