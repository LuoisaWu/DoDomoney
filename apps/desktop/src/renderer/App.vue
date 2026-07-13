<script setup lang="ts">
import { BarChart3, Bot, ClipboardList, HandCoins, LogOut, Settings, Users, WalletCards } from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";
import type { Component } from "vue";
import AccountsPage from "./pages/AccountsPage.vue";
import AuthPage from "./pages/AuthPage.vue";
import ChatPage from "./pages/ChatPage.vue";
import EntriesPage from "./pages/EntriesPage.vue";
import InsightsPage from "./pages/InsightsPage.vue";
import LoansPage from "./pages/LoansPage.vue";
import SettingsPage from "./pages/SettingsPage.vue";
import { apiClient, setApiContext } from "./services/apiClient";
import type { AssistantPersona, Entry, Ledger, LoanDraft, LoginResponse, User } from "./types";

type Page = "chat" | "entries" | "loans" | "insights" | "accounts" | "settings";

const navItems = [
  { key: "chat", label: "AI 记账", icon: Bot },
  { key: "entries", label: "账单明细", icon: ClipboardList },
  { key: "loans", label: "借款管理", icon: HandCoins },
  { key: "insights", label: "收支分析", icon: BarChart3 },
  { key: "accounts", label: "用户与账本", icon: Users },
  { key: "settings", label: "助手设置", icon: Settings }
] satisfies Array<{ key: Page; label: string; icon: Component }>;

const page = ref<Page>("chat");
const user = ref<User | null>(null);
const ledgers = ref<Ledger[]>([]);
const activeLedgerId = ref<number | null>(null);
const entries = ref<Entry[]>([]);
const loanDraft = ref<LoanDraft | null>(null);
const persona = ref<AssistantPersona>({
  user_id: 1,
  assistant_name: "账小喵",
  avatar: "猫",
  voice_style: "warm",
  snark_level: 1,
  mode: "cute",
  reply_length: "short",
  emoji_level: 1,
  proactive_insights: true,
  custom_instructions: "",
  created_at: "",
  updated_at: ""
});
const error = ref<string | null>(null);
const restoringSession = ref(true);
const activeLedger = computed(() => ledgers.value.find((ledger) => ledger.id === activeLedgerId.value) ?? null);

async function refreshEntries() {
  try {
    entries.value = await apiClient.listEntries();
    error.value = null;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "无法连接后端服务";
  }
}

function addEntry(entry: Entry) {
  entries.value = [entry, ...entries.value];
}

function updateEntry(entry: Entry) {
  entries.value = entries.value
    .map((item) => item.id === entry.id ? entry : item)
    .sort((a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime() || b.id - a.id);
}

async function deleteEntry(id: number) {
  await apiClient.deleteEntry(id);
  await refreshEntries();
}

async function changeLedger(ledger: Ledger) {
  activeLedgerId.value = ledger.id;
  setApiContext({ userId: user.value?.id, ledgerId: ledger.id, token: localStorage.getItem("dodomoney-token") || undefined });
  await refreshEntries();
}

function updateLedgers(next: Ledger[]) {
  ledgers.value = next;
}

function openLoanDraft(draft: LoanDraft) {
  loanDraft.value = draft;
  page.value = "loans";
}

async function finishAuthentication(login: LoginResponse) {
  user.value = login.user;
  ledgers.value = login.ledgers;
  activeLedgerId.value = login.active_ledger_id;
  const active = login.ledgers.find((ledger) => ledger.id === login.active_ledger_id) ?? login.ledgers[0];
  localStorage.setItem("dodomoney-token", login.token);
  setApiContext({ userId: login.user.id, ledgerId: active?.id, token: login.token });
  persona.value = await apiClient.getPersona();
  await refreshEntries();
  error.value = null;
}

async function logout() {
  try { await apiClient.logout(); } catch { /* 本地退出不应被网络错误阻止 */ }
  localStorage.removeItem("dodomoney-token");
  setApiContext({});
  user.value = null;
  ledgers.value = [];
  activeLedgerId.value = null;
  entries.value = [];
  page.value = "chat";
  error.value = null;
}

onMounted(() => {
  void (async () => {
    const token = localStorage.getItem("dodomoney-token");
    if (!token) {
      restoringSession.value = false;
      return;
    }
    try {
      setApiContext({ token });
      await finishAuthentication(await apiClient.restoreSession());
    } catch {
      localStorage.removeItem("dodomoney-token");
      setApiContext({});
    } finally {
      restoringSession.value = false;
    }
  })();
});
</script>

<template>
  <div v-if="restoringSession" class="app-loading"><div class="brand-mark"><WalletCards :size="22" /></div><span>正在打开 Dodomoney...</span></div>
  <AuthPage v-else-if="!user" @authenticated="finishAuthentication" />
  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">
          <WalletCards :size="22" />
        </div>
        <div>
          <strong>Dodomoney</strong>
          <span>钱多多 · AI 财务助手</span>
        </div>
      </div>

      <nav class="nav-list">
        <button
          v-for="item in navItems"
          :key="item.key"
          :class="['nav-item', { active: page === item.key }]"
          :title="item.label"
          @click="page = item.key"
        >
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="sidebar-note">
        <strong>今日小目标</strong>
        <span>{{ activeLedger?.name ?? "记下每一笔，月底更从容。" }}</span>
      </div>
      <div class="sidebar-profile">
        <span class="sidebar-avatar"><img v-if="user.avatar_url" :src="user.avatar_url" alt="" /><template v-else>{{ user.display_name.slice(0, 1) }}</template></span>
        <span class="sidebar-user"><strong>{{ user.display_name }}</strong><small>{{ user.email }}</small></span>
        <button title="退出登录" @click="logout"><LogOut :size="17" /></button>
      </div>
    </aside>

    <main class="main-panel">
      <div v-if="error" class="status-banner">{{ error }}</div>
      <ChatPage v-if="page === 'chat' && activeLedgerId" :persona="persona" :user="user" :ledger-id="activeLedgerId" @entry-created="addEntry" @loan-detected="openLoanDraft" />
      <EntriesPage
        v-else-if="page === 'entries'"
        :entries="entries"
        @refresh="refreshEntries"
        @delete="deleteEntry"
        @updated="updateEntry"
      />
      <InsightsPage v-else-if="page === 'insights'" :entries="entries" />
      <LoansPage v-else-if="page === 'loans' && activeLedgerId" :ledger-id="activeLedgerId" :draft="loanDraft" @draft-consumed="loanDraft = null" />
      <AccountsPage
        v-else-if="page === 'accounts' && user && activeLedgerId"
        :user="user"
        :ledgers="ledgers"
        :active-ledger-id="activeLedgerId"
        @ledger-change="changeLedger"
        @ledgers-change="updateLedgers"
      />
      <SettingsPage
        v-else
        :persona="persona"
        :user="user"
        @persona-change="persona = $event"
        @user-change="user = $event"
      />
    </main>
  </div>
</template>
