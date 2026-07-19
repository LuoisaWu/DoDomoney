<script setup lang="ts">
import { FileText, Pencil, Plus, ReceiptText, Save, Trash2, X } from "lucide-vue-next";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { apiClient } from "../services/apiClient";
import type { Reimbursement, ReimbursementCreate, ReimbursementStatus } from "../types";

const props = defineProps<{ ledgerId: number }>();
const items = ref<Reimbursement[]>([]); const showForm = ref(false); const editingId = ref<number | null>(null); const busy = ref(false); const error = ref("");
const today = () => new Date().toLocaleDateString("en-CA");
const blank = (): ReimbursementCreate => ({ merchant: "", invoice_title: "", amount: "", invoice_date: today(), category: "交通", invoice_number: "", status: "pending", note: "", image_url: null });
const form = reactive<ReimbursementCreate>(blank());
const total = computed(() => items.value.reduce((sum, item) => sum + Number(item.amount), 0));
const pendingTotal = computed(() => items.value.filter(item => item.status !== "reimbursed").reduce((sum, item) => sum + Number(item.amount), 0));
const money = (value: number | string) => Number(value).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const statusLabel = (status: ReimbursementStatus) => ({ pending: "待报销", submitted: "已提交", reimbursed: "已到账" }[status]);
async function load() { try { items.value = await apiClient.listReimbursements(); error.value = ""; } catch (err) { error.value = err instanceof Error ? err.message : "报销记录加载失败"; } }
function startCreate() { Object.assign(form, blank()); editingId.value = null; showForm.value = true; }
function startEdit(item: Reimbursement) { Object.assign(form, { merchant: item.merchant, invoice_title: item.invoice_title, amount: item.amount, invoice_date: item.invoice_date.slice(0, 10), category: item.category, invoice_number: item.invoice_number, status: item.status, note: item.note, image_url: item.image_url }); editingId.value = item.id; showForm.value = true; }
async function save() { if (!form.merchant.trim() || !Number(form.amount) || !form.invoice_date || !form.category.trim()) { error.value = "请填写商户、金额、日期和类别"; return; } busy.value = true; try { editingId.value ? await apiClient.updateReimbursement(editingId.value, { ...form }) : await apiClient.createReimbursement({ ...form }); await load(); showForm.value = false; } catch (err) { error.value = err instanceof Error ? err.message : "保存失败"; } finally { busy.value = false; } }
async function remove(item: Reimbursement) { if (!window.confirm(`删除“${item.merchant}”的报销记录？`)) return; await apiClient.deleteReimbursement(item.id); await load(); }
watch(() => props.ledgerId, () => void load()); onMounted(() => void load());
</script>

<template>
  <section class="work-area reimbursement-page">
    <header class="page-header"><div><p class="eyebrow">发票报销</p><h1>从开票到到账，进度一目了然</h1><p class="subtle">可以手动添加，也可以在 AI 记账中直接描述一张发票。</p></div><button class="primary-button page-add-button" @click="startCreate"><Plus :size="17" /> 添加报销</button></header>
    <div v-if="error" class="status-banner">{{ error }}</div>
    <div class="metric-grid"><div class="metric-card"><span>发票金额合计</span><strong>¥ {{ money(total) }}</strong><small>{{ items.length }} 张发票</small></div><div class="metric-card expense-card"><span>尚未到账</span><strong>¥ {{ money(pendingTotal) }}</strong><small>{{ items.filter(item => item.status !== 'reimbursed').length }} 笔处理中</small></div><div class="metric-card income-card"><span>已报销到账</span><strong>{{ items.filter(item => item.status === 'reimbursed').length }} 笔</strong><small>可在列表中更新状态</small></div></div>
    <div class="section-block reimbursement-list">
      <div class="section-heading"><div><h2><ReceiptText :size="18" /> 报销记录</h2><span>按发票日期倒序</span></div></div>
      <div v-if="!items.length" class="loan-empty"><FileText :size="32" /><h2>还没有报销记录</h2><p>手动添加，或在对话中说“昨天打车发票 68 元，需要报销”。</p><button class="primary-button" @click="startCreate"><Plus :size="16" /> 添加第一张发票</button></div>
      <table v-else><thead><tr><th>日期</th><th>开具单位</th><th>发票抬头</th><th>类别</th><th>发票号</th><th>状态</th><th>金额</th><th></th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td>{{ item.invoice_date }}</td><td><strong>{{ item.merchant }}</strong><small v-if="item.note" class="row-note">{{ item.note }}</small></td><td>{{ item.invoice_title || '—' }}</td><td>{{ item.category }}</td><td>{{ item.invoice_number || '—' }}</td><td><span :class="['reimbursement-status', item.status]">{{ statusLabel(item.status) }}</span></td><td class="amount">¥ {{ money(item.amount) }}</td><td><div class="row-actions"><button title="编辑" @click="startEdit(item)"><Pencil :size="15" /></button><button title="删除" @click="remove(item)"><Trash2 :size="15" /></button></div></td></tr></tbody></table>
    </div>
    <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><div class="entry-modal"><header class="entry-modal-header"><div><p class="eyebrow">{{ editingId ? '编辑报销' : '新增报销' }}</p><h2>填写发票信息</h2></div><button class="modal-close" @click="showForm = false"><X :size="20" /></button></header><form class="entry-form" @submit.prevent="save"><div class="loan-form-grid"><label class="wide">开具单位<input v-model.trim="form.merchant" required placeholder="例如：滴滴出行、某某酒店" /></label><label class="wide">发票抬头（购买方）<input v-model.trim="form.invoice_title" maxlength="120" /></label><label>发票日期<input v-model="form.invoice_date" required type="date" /></label><label>报销金额<input v-model="form.amount" required min="0.01" step="0.01" type="number" /></label><label>费用类别<input v-model.trim="form.category" required list="reimbursement-categories" /><datalist id="reimbursement-categories"><option value="交通"/><option value="餐饮"/><option value="住宿"/><option value="办公"/><option value="通讯"/></datalist></label><label>处理状态<select v-model="form.status"><option value="pending">待报销</option><option value="submitted">已提交</option><option value="reimbursed">已到账</option></select></label><label class="wide">发票号码（可选）<input v-model.trim="form.invoice_number" maxlength="80" /></label><label class="wide">备注（可选）<textarea v-model="form.note" maxlength="500"></textarea></label></div><div class="entry-modal-actions"><button type="button" class="secondary-button" @click="showForm = false">取消</button><button class="primary-button" :disabled="busy" type="submit"><Save :size="16" /> {{ busy ? '保存中...' : '保存报销' }}</button></div></form></div></div>
  </section>
</template>
