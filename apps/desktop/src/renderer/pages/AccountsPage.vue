<script setup lang="ts">
import { BookOpen, Plus, RefreshCw, UserPlus } from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import { apiClient, resolveMediaUrl } from "../services/apiClient";
import type { Ledger, LedgerMember, LedgerType, User } from "../types";

const props = defineProps<{
  user: User;
  ledgers: Ledger[];
  activeLedgerId: number;
}>();

const emit = defineEmits<{
  ledgerChange: [ledger: Ledger];
  ledgersChange: [ledgers: Ledger[]];
}>();

const ledgerTypes: Array<{ value: LedgerType; label: string }> = [
  { value: "personal", label: "个人账本" },
  { value: "family", label: "家庭账本" },
  { value: "shared", label: "共享账本" }
];

const name = ref("");
const type = ref<LedgerType>("personal");
const members = ref<LedgerMember[]>([]);
const email = ref("");
const displayName = ref("");
const busy = ref(false);
const active = computed(() => props.ledgers.find((ledger) => ledger.id === props.activeLedgerId) ?? null);

function ledgerTypeLabel(value: LedgerType) {
  return ledgerTypes.find((item) => item.value === value)?.label ?? value;
}

async function refresh() {
  const next = await apiClient.listLedgers();
  emit("ledgersChange", next);
  const current = next.find((ledger) => ledger.id === props.activeLedgerId);
  if (current) emit("ledgerChange", current);
}

async function loadMembers() {
  if (!active.value) {
    members.value = [];
    return;
  }
  try {
    members.value = await apiClient.listMembers(active.value.id);
  } catch {
    members.value = [];
  }
}

async function createLedger() {
  if (!name.value.trim()) return;
  busy.value = true;
  try {
    const created = await apiClient.createLedger(name.value.trim(), type.value);
    emit("ledgersChange", [...props.ledgers, created]);
    emit("ledgerChange", created);
    name.value = "";
  } finally {
    busy.value = false;
  }
}

async function addMember() {
  if (!active.value || !email.value.trim()) return;
  busy.value = true;
  try {
    await apiClient.addMember(active.value.id, email.value.trim(), displayName.value.trim() || undefined);
    email.value = "";
    displayName.value = "";
    await loadMembers();
    await refresh();
  } finally {
    busy.value = false;
  }
}

watch(() => props.activeLedgerId, () => {
  void loadMembers();
}, { immediate: true });
</script>

<template>
  <section class="work-area">
    <header class="page-header">
      <div class="account-heading">
        <div class="account-avatar">
          <img v-if="user.avatar_url" :src="resolveMediaUrl(user.avatar_url)" alt="用户头像" />
          <span v-else>{{ user.display_name.slice(0, 1) }}</span>
        </div>
        <div>
        <p class="eyebrow">用户与账本</p>
        <h1>管理你的账户和账本</h1>
        <p class="subtle">当前用户：{{ user.display_name }} · {{ user.email }}</p>
        </div>
      </div>
      <button class="icon-button" title="刷新" @click="refresh">
        <RefreshCw :size="18" />
      </button>
    </header>

    <div class="account-grid">
      <div class="section-block">
        <div class="section-heading">
          <h2><BookOpen :size="18" /> 我的账本</h2>
          <span>{{ ledgers.length }} 个</span>
        </div>
        <div class="ledger-list">
          <button
            v-for="ledger in ledgers"
            :key="ledger.id"
            :class="['ledger-row', { active: ledger.id === activeLedgerId }]"
            @click="emit('ledgerChange', ledger)"
          >
            <span>
              <strong>{{ ledger.name }}</strong>
              <small>{{ ledgerTypeLabel(ledger.type) }} · {{ ledger.member_count }} 人</small>
            </span>
            <em>{{ ledger.role }}</em>
          </button>
        </div>

        <div class="form-stack">
          <input v-model="name" placeholder="新账本名称" />
          <select v-model="type">
            <option v-for="item in ledgerTypes" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
          <button class="primary-button" :disabled="busy || !name.trim()" @click="createLedger">
            <Plus :size="16" />
            创建账本
          </button>
        </div>
      </div>

      <div class="section-block">
        <div class="section-heading">
          <h2><UserPlus :size="18" /> 账本成员</h2>
          <span>{{ active?.name ?? "未选择" }}</span>
        </div>
        <div class="member-list">
          <div v-for="member in members" :key="member.id" class="member-row">
            <span>
              <strong>{{ member.display_name }}</strong>
              <small>{{ member.email }}</small>
            </span>
            <em>{{ member.role }}</em>
          </div>
        </div>

        <div class="form-stack">
          <input v-model="email" placeholder="成员邮箱" />
          <input v-model="displayName" placeholder="成员显示名称（可选）" />
          <button class="primary-button" :disabled="busy || !active || !email.trim()" @click="addMember">
            <UserPlus :size="16" />
            添加成员
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
