<script setup>
import { computed, reactive, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { api, resolveMediaUrl, showError } from "../../services/api";
import { persistSession, requireLogin, session } from "../../services/session";

const saving = ref(false);
const draft = reactive({
  assistant_name: "账小喵", avatar: "🐱", voice_style: "warm", mode: "cute",
  reply_length: "short", emoji_level: 1, proactive_insights: true, custom_instructions: ""
});
const user = reactive({ display_name: "", avatar_url: "" });
const avatarUrl = computed(() => /^(https?:\/\/|\/media\/|data:image\/)/.test(draft.avatar));
const modes = ["均衡伙伴", "可爱小喵", "理性顾问", "鼓励教练", "幽默腹黑"];
const modeValues = ["balanced", "cute", "rational", "encouraging", "witty_dark"];
const voices = ["温暖亲切", "活泼俏皮", "直接利落", "沉稳克制"];
const voiceValues = ["warm", "playful", "direct", "calm"];
const lengths = ["简短确认", "适度说明", "详细反馈"];
const lengthValues = ["short", "medium", "detailed"];

async function load() {
  if (!requireLogin()) return;
  try {
    session.persona = await api.persona();
    Object.assign(draft, session.persona);
    Object.assign(user, { display_name: session.user.display_name, avatar_url: session.user.avatar_url || "" });
  } catch (error) { showError(error); }
}
async function photo(target) {
  try {
    const selected = await new Promise((resolve, reject) => uni.chooseImage({
      count: 1, sizeType: ["compressed"], success: resolve, fail: reject
    }));
    uni.showLoading({ title: "上传中" });
    const result = await api.uploadAvatar(selected.tempFilePaths[0]);
    if (target === "user") user.avatar_url = result.url; else draft.avatar = result.url;
  } catch (error) {
    if (!String(error?.errMsg).includes("cancel")) showError(error);
  } finally { uni.hideLoading(); }
}
async function save() {
  saving.value = true;
  try {
    const [persona, currentUser] = await Promise.all([
      api.updatePersona({ ...draft }),
      api.updateUser({ ...user })
    ]);
    session.persona = persona;
    session.user = currentUser;
    persistSession();
    uni.showToast({ title: "已保存" });
  } catch (error) { showError(error); }
  finally { saving.value = false; }
}
onShow(load);
</script>

<template>
  <view class="page">
    <view class="hero"><text class="eyebrow">个性与头像</text><text class="title">把助手调成喜欢的样子</text></view>
    <view class="card">
      <view class="card-title">你的资料</view>
      <view class="profile">
        <view class="avatar" @click="photo('user')"><image v-if="user.avatar_url" :src="resolveMediaUrl(user.avatar_url)" /><text v-else>{{ user.display_name?.slice(0,1) }}</text></view>
        <button class="btn small" @click="photo('user')">上传用户照片</button>
      </view>
      <label class="field">显示名称<input v-model="user.display_name" class="input" maxlength="80" /></label>
    </view>
    <view class="card">
      <view class="card-title">助手形象</view>
      <view class="profile">
        <view class="avatar assistant" @click="photo('assistant')"><image v-if="avatarUrl" :src="resolveMediaUrl(draft.avatar)" /><text v-else>{{ draft.avatar || "🐱" }}</text></view>
        <button class="btn small" @click="photo('assistant')">上传助手照片</button>
      </view>
      <label class="field">助手名称<input v-model="draft.assistant_name" class="input" maxlength="40" /></label>
    </view>
    <view class="card">
      <view class="card-title">性格与表达</view>
      <label class="field">人格模式<picker :range="modes" :value="modeValues.indexOf(draft.mode)" @change="draft.mode=modeValues[$event.detail.value]"><view class="picker">{{ modes[modeValues.indexOf(draft.mode)] }}</view></picker></label>
      <label class="field">说话语气<picker :range="voices" :value="voiceValues.indexOf(draft.voice_style)" @change="draft.voice_style=voiceValues[$event.detail.value]"><view class="picker">{{ voices[voiceValues.indexOf(draft.voice_style)] }}</view></picker></label>
      <label class="field">回复长度<picker :range="lengths" :value="lengthValues.indexOf(draft.reply_length)" @change="draft.reply_length=lengthValues[$event.detail.value]"><view class="picker">{{ lengths[lengthValues.indexOf(draft.reply_length)] }}</view></picker></label>
      <label class="field">主动财务提醒<switch :checked="draft.proactive_insights" color="#dc744d" @change="draft.proactive_insights=$event.detail.value" /></label>
      <label class="field">表情用量：{{ draft.emoji_level }} / 3<slider :value="draft.emoji_level" min="0" max="3" step="1" activeColor="#dc744d" @change="draft.emoji_level=$event.detail.value" /></label>
      <label class="field">专属要求<textarea v-model="draft.custom_instructions" class="textarea" maxlength="500" placeholder="例如：称呼我为老板；不要使用网络流行语。" /></label>
    </view>
    <button class="btn primary save" :disabled="saving" @click="save">{{ saving ? "保存中…" : "保存全部设置" }}</button>
  </view>
</template>

<style scoped>
.profile{display:flex;align-items:center;gap:24rpx;margin-bottom:26rpx}.avatar{width:100rpx;height:100rpx;display:flex;align-items:center;justify-content:center;border-radius:30rpx;background:#f0dfca;font-size:40rpx;overflow:hidden}.avatar.assistant{background:#ffe1ce}.avatar image{width:100%;height:100%;object-fit:cover}.save{width:100%;margin-bottom:30rpx}
</style>
