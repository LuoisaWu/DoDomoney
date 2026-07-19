<script setup>
import { computed, onUnmounted, reactive, ref } from "vue";
import { api, getApiBaseUrl, getConfiguredAppApiBaseUrl, setApiBaseUrl, showError } from "../../services/api";
import { persistSession, session, setLogin } from "../../services/session";

const mode = ref("login"), busy = ref(false), sending = ref(false), cooldown = ref(0), notice = ref("");
const apiBaseUrl = ref(getApiBaseUrl());
const form = reactive({ email: "", displayName: "", password: "", confirm: "", code: "" });
let timer;
const valid = computed(() => form.email.trim() && form.password.length >= 8 && (mode.value === "login" || (form.displayName.trim() && form.code.length === 6 && form.confirm === form.password)));
function switchMode(value) { mode.value = value; notice.value = ""; form.password = form.confirm = form.code = ""; }
function useUsbProxy() {
  apiBaseUrl.value = "http://127.0.0.1:8000";
  setApiBaseUrl(apiBaseUrl.value);
  uni.showToast({ title: "已切换到 USB 调试地址", icon: "none" });
}
function useHotspot() {
  apiBaseUrl.value = getConfiguredAppApiBaseUrl();
  setApiBaseUrl(apiBaseUrl.value);
  uni.showToast({ title: "已切换到热点调试地址", icon: "none" });
}
async function sendCode() {
  if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) return uni.showToast({ title: "请输入有效邮箱", icon: "none" });
  sending.value = true;
  try { const result = await api.sendCode(form.email.trim()); notice.value = result.development_code ? `开发环境验证码：${result.development_code}` : result.message; cooldown.value = result.retry_after; timer = setInterval(() => { if (--cooldown.value <= 0) clearInterval(timer); }, 1000); }
  catch (error) { showError(error, "验证码发送失败"); } finally { sending.value = false; }
}
async function submit() {
  if (!valid.value) return uni.showToast({ title: mode.value === "register" && form.confirm !== form.password ? "两次密码不一致" : "请完整填写信息", icon: "none" });
  busy.value = true;
  try {
    setApiBaseUrl(apiBaseUrl.value);
    const result = mode.value === "login" ? await api.login(form.email.trim(), form.password) : await api.register(form.email.trim(), form.displayName.trim(), form.password, form.code);
    setLogin(result);
    session.persona = await api.persona();
    session.ready = true;
    persistSession();
    console.log("[Dodomoney] 登录成功，准备进入首页", { apiBaseUrl: getApiBaseUrl(), userId: session.user?.id });
    uni.reLaunch({
      url: "/pages/index/index",
      fail: error => {
        console.error("[Dodomoney] 首页跳转失败", error);
        showError(error, "首页打开失败");
      }
    });
  } catch (error) { showError(error); } finally { busy.value = false; }
}
onUnmounted(() => clearInterval(timer));
</script>

<template>
  <view class="auth">
    <view class="brand"><image src="/static/logo.png" /><text>Dodomoney</text></view>
    <view class="welcome"><text class="kicker">你的 AI 财务搭子</text><text class="headline">每一笔小账，\n都值得被温柔记住。</text><text class="copy">聊天一样轻松记账，随时看清自己的钱都去了哪里。</text></view>
    <view class="auth-card">
      <view class="tabs"><button :class="{ active: mode === 'login' }" @click="switchMode('login')">登录</button><button :class="{ active: mode === 'register' }" @click="switchMode('register')">注册</button></view>
      <label v-if="mode === 'register'" class="field">昵称<input v-model="form.displayName" class="input" placeholder="怎么称呼你" maxlength="80" /></label>
      <label class="field">邮箱<input v-model="form.email" class="input" type="text" placeholder="name@example.com" /></label>
      <label v-if="mode === 'register'" class="field">邮箱验证码<view class="code-row"><input v-model="form.code" class="input" type="number" maxlength="6" placeholder="6 位验证码" /><button class="code" :disabled="sending || cooldown" @click="sendCode">{{ cooldown ? `${cooldown}s` : sending ? '发送中' : '发送验证码' }}</button></view></label>
      <label class="field">密码<input v-model="form.password" class="input" password placeholder="至少 8 位" maxlength="128" /></label>
      <label v-if="mode === 'register'" class="field">确认密码<input v-model="form.confirm" class="input" password placeholder="再次输入密码" /></label>
      <text v-if="notice" class="notice">{{ notice }}</text>
      <!-- #ifdef APP-PLUS -->
      <label class="field api-field">
        <view class="api-title">
          <text>后端服务地址</text>
          <view class="debug-links"><text class="debug-link" @click.stop="useHotspot">使用热点调试</text><text class="debug-link" @click.stop="useUsbProxy">使用 USB 调试</text></view>
        </view>
        <input v-model="apiBaseUrl" class="input" type="text" placeholder="http://电脑局域网IP:8000" />
        <text class="api-help">热点调试需先运行 start-phone-wifi-debug.bat；USB 调试需运行 start-phone-debug.bat。</text>
      </label>
      <!-- #endif -->
      <!-- #ifndef APP-PLUS -->
      <text class="api-hint">服务地址：{{ getApiBaseUrl() }}</text>
      <!-- #endif -->
      <button class="btn primary submit" :disabled="busy || !valid" @click="submit">{{ busy ? '请稍候…' : mode === 'login' ? '登录 Dodomoney' : '创建账户' }}</button>
    </view>
  </view>
</template>

<style scoped>
.auth { min-height: 100vh; padding: calc(80rpx + env(safe-area-inset-top)) 34rpx 50rpx; background: linear-gradient(155deg,#fff7e9,#f8e2c9 54%,#edb48e); }
.brand { display:flex;align-items:center;gap:16rpx;font-size:34rpx;font-weight:900 }.brand image{width:68rpx;height:68rpx;border-radius:20rpx}.welcome{padding:70rpx 10rpx 55rpx}.welcome text{display:block}.kicker{color:#b85c3e;font-weight:800}.headline{margin-top:22rpx;font-size:56rpx;line-height:1.35;font-weight:900;white-space:pre-line}.copy{margin-top:24rpx;color:#76685c;line-height:1.6}.auth-card{padding:34rpx;background:rgba(255,253,248,.96);border-radius:34rpx;box-shadow:0 24rpx 70rpx rgba(92,49,25,.13)}.tabs{display:flex;padding:8rpx;margin-bottom:30rpx;background:#eee7dc;border-radius:20rpx}.tabs button{flex:1;background:transparent;font-size:27rpx}.tabs .active{background:#fff;border-radius:15rpx;color:#c75f3d;font-weight:800}.code-row{display:flex;align-items:center;gap:10rpx}.code-row .input{flex:1}.code{white-space:nowrap;padding:0 14rpx;background:transparent;color:#c76341;font-size:24rpx}.notice{display:block;margin:-4rpx 0 20rpx;color:#4c8b69;font-size:24rpx}.api-hint{display:block;margin-bottom:16rpx;color:#9b9185;font-size:20rpx;word-break:break-all}.api-field{margin-top:4rpx}.api-title{display:flex;align-items:center;justify-content:space-between;gap:12rpx}.debug-links{display:flex;gap:16rpx}.debug-link{color:#c45f3e;font-size:21rpx}.api-help{display:block;margin-top:8rpx;color:#9b9185;font-size:20rpx;font-weight:400}.submit{width:100%;margin-top:8rpx}
</style>


