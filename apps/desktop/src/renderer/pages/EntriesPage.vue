<script setup lang="ts">
import { CalendarDays, RefreshCcw, Trash2, X } from "lucide-vue-next";
import { computed, reactive, ref } from "vue";
import { apiClient } from "../services/apiClient";
import type { Entry } from "../types";

const props = defineProps<{
  entries: Entry[];
}>();

const emit = defineEmits<{
  refresh: [];
  delete: [id: number];
  updated: [entry: Entry];
}>();

const selectedEntry = ref<Entry | null>(null);
const saving = ref(false);
const saveError = ref("");
const draft = reactive({ amount: "", category: "", occurred_at: "", description: "" });

const categorySuggestions = computed(() =>
  [...new Set(props.entries.map((entry) => entry.category).filter(Boolean))].sort((a, b) => a.localeCompare(b, "zh-CN"))
);

function formatTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function toLocalDateTime(value: string) {
  const date = new Date(value);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function openDetails(entry: Entry) {
  selectedEntry.value = entry;
  draft.amount = entry.amount;
  draft.category = entry.category;
  draft.occurred_at = toLocalDateTime(entry.occurred_at);
  draft.description = entry.description;
  saveError.value = "";
}

function closeDetails() {
  if (!saving.value) selectedEntry.value = null;
}

async function saveEntry() {
  if (!selectedEntry.value) return;
  saveError.value = "";
  saving.value = true;
  try {
    const updated = await apiClient.updateEntry(selectedEntry.value.id, {
      amount: draft.amount,
      category: draft.category.trim(),
      occurred_at: new Date(draft.occurred_at).toISOString(),
      description: draft.description.trim()
    });
    emit("updated", updated);
    selectedEntry.value = null;
  } catch (error) {
    saveError.value = error instanceof Error ? error.message : "保存失败，请稍后重试";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <section class="work-area">
    <header class="page-header">
      <div>
        <p class="eyebrow">账单明细</p>
        <h1>每一笔都清清楚楚</h1>
        <p class="subtle">共 {{ entries.length }} 笔记录 · 点击账单查看详情</p>
      </div>
      <button class="icon-button" title="刷新" @click="emit('refresh')">
        <RefreshCcw :size="18" />
      </button>
    </header>

    <div class="table-shell">
      <table>
        <thead>
          <tr>
            <th>时间</th>
            <th>类型</th>
            <th>分类</th>
            <th>备注</th>
            <th>金额</th>
            <th aria-label="操作" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in entries" :key="entry.id" class="entry-row" tabindex="0" @click="openDetails(entry)" @keydown.enter="openDetails(entry)">
            <td>{{ formatTime(entry.occurred_at) }}</td>
            <td>
              <span :class="['type-pill', entry.type]">
                {{ entry.type === "expense" ? "支出" : "收入" }}
              </span>
            </td>
            <td>{{ entry.subcategory ? `${entry.category} · ${entry.subcategory}` : entry.category }}</td>
            <td>{{ entry.description }}</td>
            <td :class="['amount', entry.type]">
              {{ entry.type === "expense" ? "-" : "+" }}{{ entry.amount }}
            </td>
            <td>
              <button class="table-action" title="删除" @click.stop="emit('delete', entry.id)">
                <Trash2 :size="16" />
              </button>
            </td>
          </tr>
          <tr v-if="entries.length === 0">
            <td colspan="6" class="empty-cell">还没有账单，从 AI 记账开始吧。</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="selectedEntry" class="modal-backdrop" role="presentation" @mousedown.self="closeDetails">
      <section class="entry-modal" role="dialog" aria-modal="true" aria-labelledby="entry-dialog-title">
        <header class="entry-modal-header">
          <div>
            <p class="eyebrow">账单详情</p>
            <h2 id="entry-dialog-title">查看与编辑账单</h2>
          </div>
          <button class="modal-close" type="button" aria-label="关闭" @click="closeDetails"><X :size="20" /></button>
        </header>

        <form class="entry-form" @submit.prevent="saveEntry">
          <div class="entry-meta">
            <span :class="['type-pill', selectedEntry.type]">{{ selectedEntry.type === "expense" ? "支出" : "收入" }}</span>
            <span>账单编号 #{{ selectedEntry.id }}</span>
            <span>来源：{{ selectedEntry.source === "manual" ? "手动记录" : selectedEntry.source }}</span>
          </div>

          <label>
            <span>金额</span>
            <div class="amount-input"><span>¥</span><input v-model="draft.amount" type="number" min="0.01" step="0.01" required /></div>
          </label>

          <label>
            <span>类别</span>
            <input v-model.trim="draft.category" list="entry-categories" maxlength="80" required />
            <datalist id="entry-categories"><option v-for="category in categorySuggestions" :key="category" :value="category" /></datalist>
          </label>

          <label>
            <span>日期与时间</span>
            <div class="date-input"><CalendarDays :size="17" /><input v-model="draft.occurred_at" type="datetime-local" required /></div>
          </label>

          <label>
            <span>备注</span>
            <textarea v-model.trim="draft.description" maxlength="500" rows="4" required />
            <small>{{ draft.description.length }}/500</small>
          </label>

          <p v-if="saveError" class="save-error" role="alert">{{ saveError }}</p>
          <footer class="entry-modal-actions">
            <button class="secondary-button" type="button" :disabled="saving" @click="closeDetails">取消</button>
            <button class="primary-button" type="submit" :disabled="saving">{{ saving ? "保存中…" : "保存修改" }}</button>
          </footer>
        </form>
      </section>
    </div>
  </section>
</template>
