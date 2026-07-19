<script setup>
import { onShow } from "@dcloudio/uni-app";
import { api, resolveMediaUrl } from "../../services/api";
import { clearLogin, requireLogin, session } from "../../services/session";

const links = [
  { icon: "🧾", title: "发票报销", copy: "管理从开票到到账的进度", url: "/pages/reimbursements/reimbursements" },
  { icon: "🧮", title: "个人所得税", copy: "年度综合所得税测算", url: "/pages/tax/tax" },
  { icon: "📚", title: "用户与账本", copy: "切换账本、管理共享成员", url: "/pages/accounts/accounts" },
  { icon: "🐱", title: "助手设置", copy: "头像、人格、语气与回复偏好", url: "/pages/settings/settings" }
];
function go(url) { uni.navigateTo({ url }); }
function logout() {
  uni.showModal({
    title: "退出登录", content: "确定退出当前账户吗？",
    success: async result => {
      if (!result.confirm) return;
      try { await api.logout(); } catch {}
      clearLogin();
      uni.reLaunch({ url: "/pages/auth/auth" });
    }
  });
}
onShow(requireLogin);
</script>

<template>
  <view class="page">
    <view class="profile card">
      <view class="avatar"><image v-if="session.user?.avatar_url" :src="resolveMediaUrl(session.user.avatar_url)" /><text v-else>{{ session.user?.display_name?.slice(0,1) }}</text></view>
      <view><text class="name">{{ session.user?.display_name }}</text><text class="muted">{{ session.user?.email }}</text><text class="ledger">当前：{{ session.ledgers.find(x=>x.id===session.activeLedgerId)?.name }}</text></view>
    </view>
    <view v-for="item in links" :key="item.url" class="link card" @click="go(item.url)"><text class="icon">{{ item.icon }}</text><view><text class="link-title">{{ item.title }}</text><text class="muted">{{ item.copy }}</text></view><text class="arrow">›</text></view>
    <button class="btn danger logout" @click="logout">退出登录</button>
    <text class="version">Dodomoney Phone · 1.0.0</text>
  </view>
</template>

<style scoped>
.profile{display:flex;align-items:center;gap:22rpx;margin-top:16rpx}.avatar{width:100rpx;height:100rpx;display:flex;align-items:center;justify-content:center;border-radius:30rpx;background:#f3ddc7;font-size:40rpx;overflow:hidden}.avatar image{width:100%;height:100%;object-fit:cover}.name,.link-title{display:block;font-size:32rpx;font-weight:850}.ledger{display:block;margin-top:7rpx;color:#c26949;font-size:23rpx}.link{display:flex;align-items:center;gap:22rpx}.link>view{flex:1}.icon{font-size:44rpx}.arrow{font-size:50rpx;color:#b2a79a}.logout{width:100%;margin-top:40rpx}.version{display:block;text-align:center;color:#aaa095;font-size:22rpx;margin-top:30rpx}
</style>
