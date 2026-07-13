<script setup lang="ts">
import { CalendarDays, ChevronRight, CreditCard, Pencil, Plus, Save, Trash2, X } from "lucide-vue-next";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { apiClient } from "../services/apiClient";
import type { Loan, LoanCreate, LoanDraft, RepaymentMethod } from "../types";

const props = defineProps<{ ledgerId: number; draft?: LoanDraft | null }>();
const emit = defineEmits<{ draftConsumed: [] }>();

type ScheduleItem = { period: number; dueDate: string; payment: number; principal: number; interest: number; balance: number };
const loans = ref<Loan[]>([]);
const selectedId = ref<number | null>(null);
const editingId = ref<number | null>(null);
const showForm = ref(false);
const busy = ref(false);
const error = ref("");
const today = () => new Date().toLocaleDateString("en-CA");

function addMonths(dateText: string, months: number) {
  const [year, month, day] = dateText.split("-").map(Number);
  const target = new Date(year, month - 1 + months, 1);
  const lastDay = new Date(target.getFullYear(), target.getMonth() + 1, 0).getDate();
  target.setDate(Math.min(day, lastDay));
  return target.toLocaleDateString("en-CA");
}

function nextMonth(dateText: string) { return addMonths(dateText, 1); }

const blankForm = (): LoanCreate => ({
  creditor: "", borrowed_at: today(), principal: "", repayment_months: 12, annual_rate: "0",
  repayment_method: "equal_payment", first_payment_date: nextMonth(today()), note: ""
});
const form = reactive<LoanCreate>(blankForm());

function makeSchedule(source: Pick<LoanCreate, "principal" | "repayment_months" | "annual_rate" | "repayment_method" | "first_payment_date">): ScheduleItem[] {
  const principal = Number(source.principal);
  const count = Number(source.repayment_months);
  const monthlyRate = Number(source.annual_rate) / 1200;
  if (!principal || count < 1 || !source.first_payment_date) return [];
  let balance = principal;
  const equalPayment = monthlyRate === 0
    ? principal / count
    : principal * monthlyRate * Math.pow(1 + monthlyRate, count) / (Math.pow(1 + monthlyRate, count) - 1);
  return Array.from({ length: count }, (_, index) => {
    const interest = balance * monthlyRate;
    const principalPart = source.repayment_method === "equal_principal" ? principal / count : equalPayment - interest;
    const actualPrincipal = index === count - 1 ? balance : Math.min(principalPart, balance);
    const payment = actualPrincipal + interest;
    balance = Math.max(0, balance - actualPrincipal);
    return { period: index + 1, dueDate: addMonths(source.first_payment_date, index), payment, principal: actualPrincipal, interest, balance };
  });
}

const selectedLoan = computed(() => loans.value.find(item => item.id === selectedId.value) ?? loans.value[0] ?? null);
const schedule = computed(() => selectedLoan.value ? makeSchedule(selectedLoan.value) : []);
const previewSchedule = computed(() => makeSchedule(form));
const totalPrincipal = computed(() => loans.value.reduce((sum, loan) => sum + Number(loan.principal), 0));
const totalInterest = computed(() => loans.value.reduce((sum, loan) => sum + makeSchedule(loan).reduce((s, item) => s + item.interest, 0), 0));
const nextPayment = computed(() => {
  const now = today();
  const items = loans.value.flatMap(loan => makeSchedule(loan).map(item => ({ ...item, creditor: loan.creditor })));
  return items.filter(item => item.dueDate >= now).sort((a, b) => a.dueDate.localeCompare(b.dueDate))[0] ?? null;
});
const selectedTotals = computed(() => ({
  interest: schedule.value.reduce((sum, item) => sum + item.interest, 0),
  payment: schedule.value.reduce((sum, item) => sum + item.payment, 0)
}));
const interestRatio = computed(() => {
  const total = selectedTotals.value.payment;
  return total ? Math.min(100, selectedTotals.value.interest / total * 100) : 0;
});

function money(value: number | string) {
  return Number(value).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function dateLabel(value: string) { return new Date(`${value.slice(0, 10)}T00:00:00`).toLocaleDateString("zh-CN"); }
function methodLabel(value: RepaymentMethod) { return value === "equal_payment" ? "等额本息" : "等额本金"; }

async function loadLoans() {
  try {
    loans.value = await apiClient.listLoans();
    if (!loans.value.some(item => item.id === selectedId.value)) selectedId.value = loans.value[0]?.id ?? null;
    error.value = "";
  } catch (err) { error.value = err instanceof Error ? err.message : "借款数据加载失败"; }
}

function applyDraft(draft: LoanDraft) {
  Object.assign(form, blankForm(), draft);
  if (draft.borrowed_at && !draft.first_payment_date) form.first_payment_date = nextMonth(draft.borrowed_at);
  editingId.value = null;
  showForm.value = true;
  emit("draftConsumed");
}

function startCreate() { Object.assign(form, blankForm()); editingId.value = null; showForm.value = true; }
function startEdit(loan: Loan) {
  Object.assign(form, {
    creditor: loan.creditor, borrowed_at: loan.borrowed_at.slice(0, 10), principal: loan.principal,
    repayment_months: loan.repayment_months, annual_rate: loan.annual_rate,
    repayment_method: loan.repayment_method, first_payment_date: loan.first_payment_date.slice(0, 10), note: loan.note
  });
  editingId.value = loan.id; showForm.value = true;
}
async function saveLoan() {
  if (!form.creditor.trim() || !Number(form.principal) || !form.borrowed_at || !form.first_payment_date) {
    error.value = "请填写借款来源、金额和日期"; return;
  }
  busy.value = true; error.value = "";
  try {
    const saved = editingId.value
      ? await apiClient.updateLoan(editingId.value, { ...form })
      : await apiClient.createLoan({ ...form });
    await loadLoans(); selectedId.value = saved.id; showForm.value = false;
  } catch (err) { error.value = err instanceof Error ? err.message : "保存失败"; }
  finally { busy.value = false; }
}
async function removeLoan(loan: Loan) {
  if (!window.confirm(`删除向“${loan.creditor}”的这笔借款？`)) return;
  await apiClient.deleteLoan(loan.id); await loadLoans();
}

watch(() => props.draft, value => { if (value) applyDraft(value); }, { immediate: true });
watch(() => props.ledgerId, () => void loadLoans());
onMounted(() => void loadLoans());
</script>

<template>
  <section class="work-area loans-page">
    <header class="page-header">
      <div><p class="eyebrow">借款管理</p><h1>每一笔要还的钱，都心里有数</h1><p class="subtle">记录借款来源与利率，自动生成完整还款计划。</p></div>
      <button class="primary-button loan-add-button" @click="startCreate"><Plus :size="17" /> 记一笔借款</button>
    </header>

    <div v-if="error" class="status-banner">{{ error }}</div>
    <div class="loan-metrics">
      <div class="metric-card"><span>借款本金合计</span><strong>¥ {{ money(totalPrincipal) }}</strong><small>{{ loans.length }} 笔借款</small></div>
      <div class="metric-card interest-card"><span>预计利息合计</span><strong>¥ {{ money(totalInterest) }}</strong><small>按当前还款方案测算</small></div>
      <div class="metric-card next-card"><span>最近计划还款</span><strong>{{ nextPayment ? `¥ ${money(nextPayment.payment)}` : "暂无" }}</strong><small>{{ nextPayment ? `${dateLabel(nextPayment.dueDate)} · ${nextPayment.creditor}` : "添加借款后自动计算" }}</small></div>
    </div>

    <div v-if="loans.length" class="loan-layout">
      <div class="section-block loan-list-block">
        <div class="section-heading"><div><h2>我的借款</h2><span>选择查看还款计划</span></div></div>
        <button v-for="loan in loans" :key="loan.id" :class="['loan-row', { active: selectedLoan?.id === loan.id }]" @click="selectedId = loan.id">
          <span class="loan-source-icon"><CreditCard :size="18" /></span>
          <span class="loan-row-main"><strong>{{ loan.creditor }}</strong><small>{{ dateLabel(loan.borrowed_at) }} · {{ loan.repayment_months }} 期 · 年利率 {{ loan.annual_rate }}%</small></span>
          <strong>¥ {{ money(loan.principal) }}</strong><ChevronRight :size="16" />
        </button>
      </div>

      <div v-if="selectedLoan" class="section-block loan-overview">
        <div class="section-heading"><div><h2>{{ selectedLoan.creditor }}</h2><span>{{ methodLabel(selectedLoan.repayment_method) }}</span></div><div class="loan-actions"><button title="编辑" @click="startEdit(selectedLoan)"><Pencil :size="15" /></button><button title="删除" @click="removeLoan(selectedLoan)"><Trash2 :size="15" /></button></div></div>
        <div class="cost-visual">
          <div class="donut" :style="{ '--interest': `${interestRatio * 3.6}deg` }"><span><strong>{{ interestRatio.toFixed(1) }}%</strong><small>利息占比</small></span></div>
          <dl><div><dt>借款本金</dt><dd>¥ {{ money(selectedLoan.principal) }}</dd></div><div><dt>预计利息</dt><dd>¥ {{ money(selectedTotals.interest) }}</dd></div><div><dt>预计总还款</dt><dd>¥ {{ money(selectedTotals.payment) }}</dd></div><div><dt>首期还款日</dt><dd>{{ dateLabel(selectedLoan.first_payment_date) }}</dd></div></dl>
        </div>
      </div>
    </div>

    <div v-if="selectedLoan" class="section-block schedule-block">
      <div class="section-heading"><div><h2>还款时间表</h2><span>共 {{ schedule.length }} 期，每期金额精确到分</span></div></div>
      <div class="schedule-chart" aria-label="各期还款金额图">
        <div v-for="item in schedule" :key="item.period" class="schedule-bar" :title="`第 ${item.period} 期：¥${money(item.payment)}`"><i :style="{ height: `${Math.max(10, item.payment / Math.max(...schedule.map(row => row.payment)) * 100)}%` }" /></div>
      </div>
      <div class="schedule-table"><table><thead><tr><th>期数</th><th>应还日期</th><th>应还金额</th><th>本金</th><th>利息</th><th>剩余本金</th></tr></thead><tbody><tr v-for="item in schedule" :key="item.period"><td>第 {{ item.period }} 期</td><td>{{ dateLabel(item.dueDate) }}</td><td class="amount">¥ {{ money(item.payment) }}</td><td>¥ {{ money(item.principal) }}</td><td>¥ {{ money(item.interest) }}</td><td>¥ {{ money(item.balance) }}</td></tr></tbody></table></div>
    </div>

    <div v-else class="section-block loan-empty"><CreditCard :size="32" /><h2>还没有借款记录</h2><p>可以点击右上角录入，也可以在 AI 记账页直接说“今天从某平台借了 5000 元”。</p><button class="primary-button" @click="startCreate"><Plus :size="16" /> 开始记录</button></div>

    <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false">
      <div class="entry-modal loan-modal">
        <header class="entry-modal-header"><div><p class="eyebrow">{{ editingId ? "编辑借款" : "新增借款" }}</p><h2>补全借款与还款信息</h2></div><button class="modal-close" @click="showForm = false"><X :size="20" /></button></header>
        <form class="entry-form" @submit.prevent="saveLoan">
          <div class="loan-form-grid">
            <label class="wide">向什么平台或什么人借款<input v-model.trim="form.creditor" required placeholder="例如：银行、花呗、张三" /></label>
            <label>借款日期<input v-model="form.borrowed_at" required type="date" /></label>
            <label>借款金额<div class="amount-input"><span>¥</span><input v-model="form.principal" required min="0.01" step="0.01" type="number" /></div></label>
            <label>计划还款期数<input v-model.number="form.repayment_months" required min="1" max="600" type="number" /></label>
            <label>年利率（%）<input v-model="form.annual_rate" required min="0" max="100" step="0.01" type="number" /></label>
            <label>还款方式<select v-model="form.repayment_method"><option value="equal_payment">等额本息</option><option value="equal_principal">等额本金</option></select></label>
            <label>首次还款日<div class="date-input"><CalendarDays :size="16" /><input v-model="form.first_payment_date" required type="date" /></div></label>
            <label class="wide">备注（可选）<textarea v-model="form.note" maxlength="500" placeholder="合同号、用途或其他提醒"></textarea></label>
          </div>
          <div v-if="previewSchedule.length" class="loan-form-preview"><span>首期预计还款 <strong>¥ {{ money(previewSchedule[0].payment) }}</strong></span><span>预计总利息 <strong>¥ {{ money(previewSchedule.reduce((sum, item) => sum + item.interest, 0)) }}</strong></span><span>最后还款日 <strong>{{ dateLabel(previewSchedule[previewSchedule.length - 1].dueDate) }}</strong></span></div>
          <div class="entry-modal-actions"><button type="button" class="secondary-button" @click="showForm = false">取消</button><button class="primary-button" :disabled="busy" type="submit"><Save :size="16" /> {{ busy ? "保存中..." : "保存借款" }}</button></div>
        </form>
      </div>
    </div>
  </section>
</template>
