<script setup lang="ts">
import { Bot, SendHorizontal, Trash2 } from "lucide-vue-next";
import { nextTick, ref, watch } from "vue";
import { apiClient } from "../services/apiClient";
import type { AssistantPersona, ChatMessage, Entry, LoanFollowUpField, ParsedLoan, ParsedTransaction, User } from "../types";

const props = defineProps<{ persona: AssistantPersona; user: User; ledgerId: number }>();
const emit = defineEmits<{ entryCreated: [entry: Entry] }>();

const message = ref("");
const busy = ref(false);
const loading = ref(true);
const pendingContext = ref<ParsedTransaction | null>(null);
const pendingLoan = ref<ParsedLoan | null>(null);
const messages = ref<ChatMessage[]>([]);
const messageList = ref<HTMLElement | null>(null);

function isAvatarUrl(value: string) { return /^(https?:\/\/|data:image\/)/.test(value); }
function userInitial() { return props.user.display_name.trim().slice(0, 1).toUpperCase() || "我"; }
function formatTime(value?: string | null) {
  if (!value) return "待补充";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("zh-CN", { hour12: false });
}
function fieldLabel(value: ParsedTransaction["follow_up_fields"][number]) {
  return { amount: "金额", category: "类别", occurred_at: "时间", type: "收支类型" }[value];
}
function loanFieldLabel(value: LoanFollowUpField) {
  return { creditor: "出借方", borrowed_at: "借款日期", principal: "本金", repayment_months: "还款期数", annual_rate: "年利率", repayment_method: "还款方式", first_payment_date: "首次还款日" }[value];
}
function repaymentMethod(value?: ParsedLoan["repayment_method"]) {
  return value === "equal_payment" ? "等额本息" : value === "equal_principal" ? "等额本金" : "待补充";
}
async function scrollToBottom() {
  await nextTick();
  if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight;
}
async function loadHistory() {
  loading.value = true;
  try {
    messages.value = await apiClient.listChatMessages();
    const lastAssistant = [...messages.value].reverse().find((item) => item.role === "assistant");
    pendingContext.value = lastAssistant?.parsed?.follow_up_fields.length ? lastAssistant.parsed : null;
    pendingLoan.value = lastAssistant?.parsed_loan && (lastAssistant.parsed_loan.follow_up_fields.length || lastAssistant.parsed_loan.awaiting_confirmation) ? lastAssistant.parsed_loan : null;
    await scrollToBottom();
  } finally { loading.value = false; }
}
async function clearHistory() {
  if (!window.confirm("清空当前账本的全部对话记录？账单不会被删除。")) return;
  await apiClient.clearChatMessages();
  messages.value = [];
  pendingContext.value = null;
  pendingLoan.value = null;
}
function cancelFollowUp() {
  if (pendingLoan.value) {
    message.value = "取消";
    void submit();
    return;
  }
  pendingContext.value = null;
  messages.value.push({ id: Date.now(), role: "assistant", content: "已取消补充这笔账，你可以重新说一笔。", recorded: false, created_at: new Date().toISOString() });
  void scrollToBottom();
}
async function submit() {
  const text = message.value.trim();
  if (!text || busy.value) return;
  message.value = "";
  busy.value = true;
  messages.value.push({ id: Date.now(), role: "user", content: text, recorded: false, created_at: new Date().toISOString() });
  await scrollToBottom();
  try {
    const result = await apiClient.recordFromChat(text, pendingContext.value, pendingLoan.value);
    if (result.entry) emit("entryCreated", result.entry);
    pendingContext.value = result.needs_follow_up ? result.parsed ?? null : null;
    pendingLoan.value = result.needs_follow_up ? result.parsed_loan ?? null : null;
    messages.value.push({ id: Date.now() + 1, role: "assistant", content: result.reply, parsed: result.parsed, parsed_loan: result.parsed_loan, recorded: Boolean(result.entry || result.loan_id), created_at: new Date().toISOString() });
  } catch (err) {
    messages.value.push({ id: Date.now() + 1, role: "assistant", content: err instanceof Error ? err.message : "记账失败，请稍后再试。", recorded: false, created_at: new Date().toISOString() });
  } finally { busy.value = false; await scrollToBottom(); }
}

function confirmLoan() {
  message.value = "确认";
  void submit();
}

watch(() => props.ledgerId, () => void loadHistory(), { immediate: true });
</script>

<template>
  <section class="work-area">
    <header class="page-header">
      <div>
        <p class="eyebrow">AI 记账助手</p>
        <h1>说一句话，账单就记好了</h1>
        <p class="subtle">例如：今天午饭 22 元，或收到工资 8000 元。</p>
      </div>
      <div class="chat-header-actions">
        <button class="clear-chat" :disabled="!messages.length" title="清空对话" @click="clearHistory"><Trash2 :size="16" /> 清空对话</button>
        <div class="assistant-chip">
          <Bot :size="17" />
          <img v-if="isAvatarUrl(persona.avatar)" :src="persona.avatar" alt="" class="chip-avatar" />
          <span v-else>{{ persona.avatar }}</span>{{ persona.assistant_name }}在线
        </div>
      </div>
    </header>

    <div class="chat-panel">
      <div ref="messageList" class="message-list">
        <div v-if="loading" class="empty-copy">正在恢复对话...</div>
        <div v-else-if="!messages.length" class="message-row assistant">
          <span class="chat-avatar assistant-avatar"><img v-if="isAvatarUrl(persona.avatar)" :src="persona.avatar" alt="" /><template v-else>{{ persona.avatar }}</template></span>
          <div class="message-content"><small>{{ persona.assistant_name }}</small><div class="message assistant">你好，我是{{ persona.assistant_name }}。告诉我一笔收支，剩下的交给我。</div></div>
        </div>
        <div v-for="item in messages" :key="item.id" :class="['message-row', item.role]">
          <span class="chat-avatar" :class="item.role === 'assistant' ? 'assistant-avatar' : 'user-avatar'">
            <img v-if="item.role === 'assistant' && isAvatarUrl(persona.avatar)" :src="persona.avatar" alt="" />
            <img v-else-if="item.role === 'user' && user.avatar_url" :src="user.avatar_url" alt="" />
            <template v-else>{{ item.role === "assistant" ? persona.avatar : userInitial() }}</template>
          </span>
          <div class="message-content">
            <small>{{ item.role === "assistant" ? persona.assistant_name : user.display_name }}</small>
            <div :class="['message', item.role]">
              <div>{{ item.content }}</div>
              <div v-if="item.parsed" class="parse-card">
                <div class="parse-card-title"><strong>{{ item.recorded ? "已结构化并入账" : "等待补充" }}</strong><span>置信度 {{ Math.round(item.parsed.confidence * 100) }}%</span></div>
                <dl>
                  <div><dt>金额</dt><dd>{{ item.parsed.amount ? `¥${item.parsed.amount}` : "待补充" }}</dd></div>
                  <div><dt>类别</dt><dd>{{ item.parsed.category || "待补充" }}</dd></div>
                  <div><dt>类型</dt><dd>{{ item.parsed.type === "income" ? "收入" : item.parsed.type === "expense" ? "支出" : "待补充" }}</dd></div>
                  <div><dt>时间</dt><dd>{{ formatTime(item.parsed.occurred_at) }}</dd></div>
                </dl>
                <p v-if="item.parsed.follow_up_fields.length">待补字段：{{ item.parsed.follow_up_fields.map(fieldLabel).join("、") }}</p>
              </div>
              <div v-if="item.parsed_loan" class="parse-card loan-parse-card">
                <div class="parse-card-title"><strong>{{ item.recorded ? "借款已入库" : item.parsed_loan.awaiting_confirmation ? "等待确认" : "正在收集借款信息" }}</strong><span>置信度 {{ Math.round(item.parsed_loan.confidence * 100) }}%</span></div>
                <dl>
                  <div><dt>本金</dt><dd>{{ item.parsed_loan.principal ? `¥${item.parsed_loan.principal}` : "待补充" }}</dd></div>
                  <div><dt>出借方</dt><dd>{{ item.parsed_loan.creditor || "待补充" }}</dd></div>
                  <div><dt>借款日期</dt><dd>{{ item.parsed_loan.borrowed_at || "待补充" }}</dd></div>
                  <div><dt>还款期数</dt><dd>{{ item.parsed_loan.repayment_months ? `${item.parsed_loan.repayment_months} 期` : "待补充" }}</dd></div>
                  <div><dt>年利率</dt><dd>{{ item.parsed_loan.annual_rate != null ? `${item.parsed_loan.annual_rate}%` : "待补充" }}</dd></div>
                  <div><dt>还款方式</dt><dd>{{ repaymentMethod(item.parsed_loan.repayment_method) }}</dd></div>
                  <div><dt>首次还款日</dt><dd>{{ item.parsed_loan.first_payment_date || "待补充" }}</dd></div>
                </dl>
                <p v-if="item.parsed_loan.follow_up_fields.length">待补字段：{{ item.parsed_loan.follow_up_fields.map(loanFieldLabel).join("、") }}</p>
              </div>
            </div>
          </div>
        </div>
        <div v-if="busy" class="message-row assistant">
          <span class="chat-avatar assistant-avatar"><img v-if="isAvatarUrl(persona.avatar)" :src="persona.avatar" alt="" /><template v-else>{{ persona.avatar }}</template></span>
          <div class="message-content"><small>{{ persona.assistant_name }}</small><div class="message assistant typing">正在整理这笔账...</div></div>
        </div>
      </div>
      <form class="composer" @submit.prevent="submit">
        <div v-if="pendingContext || pendingLoan" class="pending-context"><span>{{ pendingLoan?.awaiting_confirmation ? '借款信息已完整，请确认或直接输入修改内容' : `正在补充上一笔：${pendingLoan ? pendingLoan.follow_up_fields.map(loanFieldLabel).join('、') : pendingContext?.follow_up_fields.map(fieldLabel).join('、')}` }}</span><div class="pending-actions"><button v-if="pendingLoan?.awaiting_confirmation" type="button" class="confirm-loan-button" :disabled="busy" @click="confirmLoan">确认入库</button><button type="button" class="cancel-follow-up" @click="cancelFollowUp">取消</button></div></div>
        <input v-model="message" :placeholder="pendingLoan?.awaiting_confirmation ? '如需修改，直接说：利率改成 3.5%' : pendingLoan ? (pendingLoan.follow_up_question || '补充借款信息') : pendingContext ? '补充缺少的信息，例如：23 元' : '输入消费、收入或借款，例如：今天从某平台借了 5000 元'" />
        <button type="submit" :disabled="busy || !message.trim()" title="发送"><SendHorizontal :size="18" /></button>
      </form>
    </div>
  </section>
</template>
