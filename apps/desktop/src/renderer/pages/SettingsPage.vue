<script setup lang="ts">
import { Camera, UserRound } from "lucide-vue-next";
import { computed, reactive, ref, watch } from "vue";
import { apiClient } from "../services/apiClient";
import type { AssistantPersona, PersonaMode, ReplyLength, User, VoiceStyle } from "../types";

const props = defineProps<{ persona: AssistantPersona; user: User | null }>();
const emit = defineEmits<{ personaChange: [persona: AssistantPersona]; userChange: [user: User] }>();
const draft = reactive({ ...props.persona });
const userDraft = reactive({ display_name: props.user?.display_name ?? "", avatar_url: props.user?.avatar_url ?? "" });
const saving = ref(false);
const uploading = ref<"assistant" | "user" | null>(null);
const saved = ref(false);
const error = ref<string | null>(null);
const avatarIsUrl = computed(() => /^(https?:\/\/|data:image\/)/.test(draft.avatar));

watch(() => props.persona, (value) => Object.assign(draft, value), { deep: true });
watch(() => props.user, (value) => { if (value) Object.assign(userDraft, { display_name: value.display_name, avatar_url: value.avatar_url ?? "" }); }, { deep: true });

const modeOptions: Array<{ value: PersonaMode; label: string; hint: string }> = [
  { value: "balanced", label: "均衡伙伴", hint: "在清晰分析和日常陪伴之间自然切换" },
  { value: "cute", label: "可爱小喵", hint: "轻松活泼，带一点小猫式表达" },
  { value: "rational", label: "理性顾问", hint: "关注数字、趋势和消费判断" },
  { value: "encouraging", label: "鼓励教练", hint: "温柔正向，帮助你持续记账" }
];
const voiceOptions: Array<{ value: VoiceStyle; label: string }> = [
  { value: "warm", label: "温暖亲切" }, { value: "playful", label: "活泼俏皮" },
  { value: "direct", label: "直接利落" }, { value: "calm", label: "沉稳克制" }
];
const lengthOptions: Array<{ value: ReplyLength; label: string }> = [
  { value: "short", label: "简短确认" }, { value: "medium", label: "适度说明" }, { value: "detailed", label: "详细反馈" }
];

async function upload(event: Event, target: "assistant" | "user") {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  uploading.value = target; error.value = null;
  try {
    const result = await apiClient.uploadAvatar(file);
    if (target === "assistant") draft.avatar = result.url; else userDraft.avatar_url = result.url;
  } catch (err) { error.value = err instanceof Error ? err.message : "头像上传失败"; }
  finally { uploading.value = null; input.value = ""; }
}
async function save() {
  saving.value = true; saved.value = false; error.value = null;
  try {
    const [persona, user] = await Promise.all([
      apiClient.updatePersona({ ...draft }),
      apiClient.updateCurrentUser({ display_name: userDraft.display_name, avatar_url: userDraft.avatar_url || undefined })
    ]);
    emit("personaChange", persona); emit("userChange", user); saved.value = true;
  } catch (err) { error.value = err instanceof Error ? err.message : "保存失败"; }
  finally { saving.value = false; }
}
</script>

<template>
  <section class="work-area">
    <header class="page-header"><div><p class="eyebrow">个性与头像</p><h1>把账小喵调成你喜欢的样子</h1><p class="subtle">头像、表达方式和个性偏好都会保存在当前用户账户中。</p></div></header>
    <form class="settings-panel persona-form" @submit.prevent="save">
      <h2 class="settings-section-title">你的资料</h2>
      <div class="profile-row">
        <div class="avatar persona-avatar user-avatar"><img v-if="userDraft.avatar_url" :src="userDraft.avatar_url" alt="用户头像" /><UserRound v-else :size="24" /></div>
        <label class="upload-button"><Camera :size="16" />{{ uploading === "user" ? "上传中..." : "上传用户照片" }}<input type="file" accept="image/png,image/jpeg,image/webp,image/gif" :disabled="Boolean(uploading)" @change="upload($event, 'user')" /></label>
        <label class="grow-label">显示名称<input v-model.trim="userDraft.display_name" maxlength="80" required /></label>
      </div>

      <div class="settings-divider"></div>
      <h2 class="settings-section-title">助手形象</h2>
      <div class="profile-row">
        <div class="avatar persona-avatar"><img v-if="avatarIsUrl" :src="draft.avatar" alt="助手头像" /><span v-else>{{ draft.avatar || "🐱" }}</span></div>
        <label class="upload-button"><Camera :size="16" />{{ uploading === "assistant" ? "上传中..." : "上传账小喵照片" }}<input type="file" accept="image/png,image/jpeg,image/webp,image/gif" :disabled="Boolean(uploading)" @change="upload($event, 'assistant')" /></label>
        <label class="grow-label">助手名称<input v-model.trim="draft.assistant_name" maxlength="40" required /></label>
      </div>

      <div class="settings-divider"></div>
      <h2 class="settings-section-title">性格与表达</h2>
      <div class="settings-grid">
        <label>人格模式<select v-model="draft.mode"><option v-for="option in modeOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
        <label>说话语气<select v-model="draft.voice_style"><option v-for="option in voiceOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
        <label>回复长度<select v-model="draft.reply_length"><option v-for="option in lengthOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
        <label>主动财务提醒<select v-model="draft.proactive_insights"><option :value="true">开启</option><option :value="false">关闭</option></select></label>
      </div>
      <p class="settings-hint">{{ modeOptions.find((option) => option.value === draft.mode)?.hint }}</p>
      <div class="range-grid">
        <label class="range-label"><span>吐槽程度 <strong>{{ draft.snark_level }}/5</strong></span><input v-model.number="draft.snark_level" type="range" min="0" max="5" step="1" /></label>
        <label class="range-label"><span>表情用量 <strong>{{ draft.emoji_level }}/3</strong></span><input v-model.number="draft.emoji_level" type="range" min="0" max="3" step="1" /></label>
      </div>
      <label class="custom-instructions">专属要求<textarea v-model.trim="draft.custom_instructions" maxlength="500" rows="3" placeholder="例如：称呼我为老板；不要使用网络流行语；每周提醒我复盘餐饮开销。"></textarea><small>{{ draft.custom_instructions.length }}/500</small></label>

      <div class="settings-actions"><button class="primary-button" type="submit" :disabled="saving || Boolean(uploading)">{{ saving ? "保存中..." : "保存全部设置" }}</button><span v-if="saved" class="save-success">已保存</span><span v-if="error" class="save-error">{{ error }}</span></div>
    </form>
  </section>
</template>
