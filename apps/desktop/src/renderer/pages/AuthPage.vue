<script setup lang="ts">
import { Eye, EyeOff, KeyRound, LockKeyhole, Mail, Sparkles, UserRound } from "lucide-vue-next";
import { computed, onBeforeUnmount, ref } from "vue";
import { apiClient } from "../services/apiClient";
import type { LoginResponse } from "../types";
import { billBuddyLogo } from "../brandAssets";

const emit = defineEmits<{ authenticated: [response: LoginResponse] }>();
const mode = ref<"login" | "register">("login");
const email = ref("");
const displayName = ref("");
const password = ref("");
const confirmPassword = ref("");
const verificationCode = ref("");
const revealPassword = ref(false);
const busy = ref(false);
const sendingCode = ref(false);
const cooldown = ref(0);
const error = ref("");
const notice = ref("");
let countdownTimer: ReturnType<typeof setInterval> | undefined;

const submitLabel = computed(() => busy.value ? "请稍候..." : mode.value === "login" ? "登录 Dodomoney" : "创建账户");

function switchMode(next: "login" | "register") {
  mode.value = next;
  error.value = "";
  notice.value = "";
  verificationCode.value = "";
  password.value = "";
  confirmPassword.value = "";
}

function startCountdown(seconds: number) {
  cooldown.value = seconds;
  if (countdownTimer) clearInterval(countdownTimer);
  countdownTimer = setInterval(() => {
    cooldown.value -= 1;
    if (cooldown.value <= 0 && countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = undefined;
    }
  }, 1000);
}

async function sendCode() {
  error.value = "";
  notice.value = "";
  const normalizedEmail = email.value.trim();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
    error.value = "请先输入有效的邮箱地址";
    return;
  }
  sendingCode.value = true;
  try {
    const response = await apiClient.sendVerificationCode(normalizedEmail);
    startCountdown(response.retry_after);
    notice.value = response.development_code
      ? `开发环境验证码：${response.development_code}`
      : response.message;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "验证码发送失败，请稍后再试";
  } finally {
    sendingCode.value = false;
  }
}

onBeforeUnmount(() => {
  if (countdownTimer) clearInterval(countdownTimer);
});

async function submit() {
  error.value = "";
  if (mode.value === "register" && password.value !== confirmPassword.value) {
    error.value = "两次输入的密码不一致";
    return;
  }
  busy.value = true;
  try {
    const response = mode.value === "login"
      ? await apiClient.login(email.value.trim(), password.value)
      : await apiClient.register(email.value.trim(), displayName.value.trim(), password.value, verificationCode.value);
    emit("authenticated", response);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "操作失败，请稍后再试";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-welcome">
      <div class="auth-brand"><span><img :src="billBuddyLogo" alt="Dodomoney" /></span><strong>Dodomoney</strong></div>
      <div class="auth-copy">
        <div class="auth-kicker"><Sparkles :size="15" /> 你的 AI 财务搭子</div>
        <h1>每一笔小账，<br />都值得被温柔记住。</h1>
        <p>聊天一样轻松记账，随时看清自己的钱都去了哪里。</p>
      </div>
      <div class="auth-preview">
        <span class="preview-avatar">🐱</span>
        <div><small>账小喵</small><p>今天午饭 28 元，已经帮你记好啦 ☀️</p></div>
      </div>
    </section>

    <section class="auth-form-side">
      <form class="auth-card" @submit.prevent="submit">
        <div class="auth-card-heading">
          <h2>{{ mode === "login" ? "欢迎回来" : "创建你的账户" }}</h2>
          <p>{{ mode === "login" ? "登录后继续管理你的账本" : "从今天开始，让每笔收支都有迹可循" }}</p>
        </div>

        <div class="auth-tabs" role="tablist">
          <button type="button" :class="{ active: mode === 'login' }" @click="switchMode('login')">登录</button>
          <button type="button" :class="{ active: mode === 'register' }" @click="switchMode('register')">注册</button>
        </div>

        <label v-if="mode === 'register'" class="auth-field">
          <span>昵称</span>
          <div><UserRound :size="18" /><input v-model="displayName" required maxlength="80" placeholder="怎么称呼你" autocomplete="name" /></div>
        </label>
        <label class="auth-field">
          <span>邮箱</span>
          <div><Mail :size="18" /><input v-model="email" required type="email" maxlength="255" placeholder="name@example.com" autocomplete="email" /></div>
        </label>
        <label v-if="mode === 'register'" class="auth-field">
          <span>邮箱验证码</span>
          <div class="verification-control">
            <KeyRound :size="18" />
            <input v-model="verificationCode" required inputmode="numeric" pattern="\d{6}" maxlength="6" placeholder="6 位验证码" autocomplete="one-time-code" />
            <button type="button" class="send-code" :disabled="sendingCode || cooldown > 0" @click="sendCode">
              {{ sendingCode ? "发送中..." : cooldown > 0 ? `${cooldown}s 后重发` : "发送验证码" }}
            </button>
          </div>
        </label>
        <label class="auth-field">
          <span>密码</span>
          <div><LockKeyhole :size="18" /><input v-model="password" required :type="revealPassword ? 'text' : 'password'" minlength="8" maxlength="128" placeholder="至少 8 位" :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" /><button type="button" class="password-toggle" :title="revealPassword ? '隐藏密码' : '显示密码'" @click="revealPassword = !revealPassword"><EyeOff v-if="revealPassword" :size="18" /><Eye v-else :size="18" /></button></div>
        </label>
        <label v-if="mode === 'register'" class="auth-field">
          <span>确认密码</span>
          <div><LockKeyhole :size="18" /><input v-model="confirmPassword" required :type="revealPassword ? 'text' : 'password'" minlength="8" maxlength="128" placeholder="再次输入密码" autocomplete="new-password" /></div>
        </label>

        <p v-if="notice" class="auth-notice">{{ notice }}</p>
        <p v-if="error" class="auth-error">{{ error }}</p>
        <button class="auth-submit" type="submit" :disabled="busy">{{ submitLabel }}</button>
        <p class="auth-switch">{{ mode === "login" ? "还没有账户？" : "已经有账户？" }}<button type="button" @click="switchMode(mode === 'login' ? 'register' : 'login')">{{ mode === "login" ? "立即注册" : "返回登录" }}</button></p>
      </form>
    </section>
  </main>
</template>
