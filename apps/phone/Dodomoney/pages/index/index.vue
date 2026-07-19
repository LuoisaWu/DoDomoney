<script setup>
import { nextTick, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { api, resolveMediaUrl, showError } from "../../services/api";
import { persistSession, requireLogin, session } from "../../services/session";

const messages = ref([]), text = ref(""), busy = ref(false), loading = ref(true), scrollId = ref("");
const pending = ref(null), pendingLoan = ref(null), pendingReimbursement = ref(null), imageContext = ref(null);
function assistant() { return session.persona || { assistant_name: "账小喵", avatar: "🐱" }; }
function avatarUrl(value) { return /^(https?:\/\/|\/media\/|data:image\/)/.test(value || ""); }
function scroll() { nextTick(() => { scrollId.value = `message-${messages.value[messages.value.length - 1]?.id || 0}`; }); }
async function load() {
  if (!requireLogin()) return;
  loading.value = true;
  try {
    if (!session.persona) session.persona = await api.persona();
    messages.value = await api.messages();
    const last = [...messages.value].reverse().find(item => item.role === "assistant");
    pending.value = !last?.recorded && last?.parsed?.follow_up_fields?.length ? last.parsed : null;
    pendingLoan.value = !last?.recorded && last?.parsed_loan && (last.parsed_loan.follow_up_fields?.length || last.parsed_loan.awaiting_confirmation) ? last.parsed_loan : null;
    pendingReimbursement.value = !last?.recorded && last?.parsed_reimbursement && (last.parsed_reimbursement.follow_up_fields?.length || last.parsed_reimbursement.awaiting_confirmation) ? last.parsed_reimbursement : null;
    scroll();
  } catch (error) { showError(error); } finally { loading.value = false; }
}
async function chooseImage() {
  try {
    let filePath = "";
    // 微信小程序优先使用 chooseMedia；其余端沿用跨端 chooseImage。
    // #ifdef MP-WEIXIN
    const selected = await new Promise((resolve, reject) => uni.chooseMedia({ count: 1, mediaType: ["image"], sizeType: ["compressed"], success: resolve, fail: reject }));
    filePath = selected.tempFiles[0].tempFilePath;
    // #endif
    // #ifndef MP-WEIXIN
    const selected = await new Promise((resolve, reject) => uni.chooseImage({ count: 1, sizeType: ["compressed"], success: resolve, fail: reject }));
    filePath = selected.tempFilePaths[0];
    // #endif
    uni.showLoading({ title: "添加图片中" }); imageContext.value = await api.uploadDocument(filePath);
  } catch (error) { if (!String(error?.errMsg).includes("cancel")) showError(error, "图片上传失败"); } finally { uni.hideLoading(); }
}
async function send(forceText) {
  const content = (forceText || text.value).trim() || (imageContext.value ? "请识别并记录这张单据" : "");
  if (!content || busy.value) return;
  text.value = ""; busy.value = true; const image = imageContext.value; imageContext.value = null;
  messages.value.push({ id: Date.now(), role: "user", content, image_url: image?.image_url, created_at: new Date().toISOString() }); scroll();
  try {
    const result = await api.record(content, pending.value, pendingLoan.value, pendingReimbursement.value, image);
    pending.value = result.needs_follow_up ? result.parsed : null; pendingLoan.value = result.needs_follow_up ? result.parsed_loan : null; pendingReimbursement.value = result.needs_follow_up ? result.parsed_reimbursement : null;
    messages.value.push({ id: Date.now()+1, role: "assistant", content: result.reply, parsed: result.parsed, parsed_loan: result.parsed_loan, parsed_reimbursement: result.parsed_reimbursement, recorded: Boolean(result.entry || result.loan_id || result.reimbursement_id), created_at: new Date().toISOString() }); scroll();
  } catch (error) {
    if (!text.value) text.value = content === "请识别并记录这张单据" ? "" : content;
    if (!imageContext.value) imageContext.value = image;
    showError(error);
  } finally { busy.value = false; }
}
function confirmPending() { send("确认"); }
function cancelPending() { send("取消"); }
async function chooseLedger(event) {
  const ledger = session.ledgers[Number(event.detail.value)];
  if (!ledger || ledger.id === session.activeLedgerId) return;
  session.activeLedgerId = ledger.id;
  persistSession();
  messages.value = [];
  pending.value = pendingLoan.value = pendingReimbursement.value = null;
  imageContext.value = null;
  await load();
  uni.showToast({ title: `已切换到${ledger.name}`, icon: "none" });
}
function clear() { uni.showModal({ title: "清空对话", content: "账单不会被删除，确定清空当前账本的对话吗？", success: async r => { if (r.confirm) { await api.clearMessages(); messages.value = []; pending.value = pendingLoan.value = pendingReimbursement.value = null; } } }); }
onShow(load);
</script>

<template>
  <view class="chat-page">
    <view class="chat-head">
      <view class="head-copy"><text class="eyebrow">AI 记账</text><text class="chat-title">{{ assistant().assistant_name }}</text><text class="ledger">{{ session.ledgers.find(x=>x.id===session.activeLedgerId)?.name || '当前账本' }}</text></view>
      <view class="head-actions">
        <picker :range="session.ledgers.map(x => x.name)" :value="Math.max(0, session.ledgers.findIndex(x => x.id === session.activeLedgerId))" :disabled="busy || loading || !session.ledgers.length" @change="chooseLedger">
          <view :class="['ledger-picker-button', { disabled: busy || loading || !session.ledgers.length }]"><text>选择账本</text><text class="chevron">⌄</text></view>
        </picker>
        <button class="clear" @click="clear">清空</button>
      </view>
    </view>
    <view v-if="session.startupError" class="network-warning" @click="session.startupError=''">{{ session.startupError }}</view>
    <scroll-view class="messages" scroll-y :scroll-into-view="scrollId" :scroll-with-animation="true">
      <view v-if="!loading && !messages.length" class="welcome card"><text class="avatar">{{ assistant().avatar || '🐱' }}</text><text>你好，我是{{ assistant().assistant_name }}。</text><text class="muted">告诉我一笔收支、借款或报销，剩下的交给我。</text></view>
      <view v-for="item in messages" :id="`message-${item.id}`" :key="item.id" :class="['message-row', item.role]">
        <view class="mini-avatar"><image v-if="item.role==='assistant' && avatarUrl(assistant().avatar)" :src="resolveMediaUrl(assistant().avatar)" /><image v-else-if="item.role==='user' && session.user?.avatar_url" :src="resolveMediaUrl(session.user.avatar_url)" /><text v-else>{{ item.role==='assistant' ? assistant().avatar : session.user?.display_name?.slice(0,1) }}</text></view>
        <view :class="['bubble', item.role]"><image v-if="item.image_url" class="document" :src="resolveMediaUrl(item.image_url)" mode="aspectFill" /><text>{{ item.content }}</text>
          <view v-if="item.parsed" class="parse"><text>{{ item.recorded ? '已入账' : '等待补充' }} · 置信度 {{ Math.round(item.parsed.confidence*100) }}%</text><view class="parse-grid"><text>¥{{ item.parsed.amount || '—' }}</text><text>{{ item.parsed.category || '待分类' }}</text><text>{{ item.parsed.type === 'income' ? '收入' : '支出' }}</text><text>{{ item.parsed.target_ledger_name || '' }}</text></view></view>
          <view v-if="item.parsed_loan" class="parse"><text>{{ item.recorded ? '借款已入库' : '借款信息' }}</text><view class="parse-grid"><text>¥{{ item.parsed_loan.principal || '—' }}</text><text>{{ item.parsed_loan.creditor || '待补出借方' }}</text><text>{{ item.parsed_loan.repayment_months || '—' }} 期</text><text>{{ item.parsed_loan.annual_rate || 0 }}%</text></view></view>
          <view v-if="item.parsed_reimbursement" class="parse"><text>{{ item.recorded ? '报销已入库' : '报销信息' }}</text><view class="parse-grid"><text>¥{{ item.parsed_reimbursement.amount || '—' }}</text><text>开具：{{ item.parsed_reimbursement.merchant || '待补充' }}</text><text>抬头：{{ item.parsed_reimbursement.invoice_title || '未识别' }}</text><text>{{ item.parsed_reimbursement.category || '待分类' }}</text></view></view>
        </view>
      </view>
      <view v-if="busy" class="message-row assistant"><view class="mini-avatar"><image v-if="avatarUrl(assistant().avatar)" :src="resolveMediaUrl(assistant().avatar)" /><text v-else>{{ assistant().avatar || '🐱' }}</text></view><view class="bubble assistant">正在整理这笔账…</view></view>
      <view style="height:20rpx" />
    </scroll-view>
    <view class="composer-wrap">
      <view v-if="pending || pendingLoan || pendingReimbursement" class="pending"><text>{{ pendingLoan?.awaiting_confirmation || pendingReimbursement?.awaiting_confirmation ? '信息已完整，请确认入库' : '正在补充上一条记录' }}</text><view><button v-if="pendingLoan?.awaiting_confirmation || pendingReimbursement?.awaiting_confirmation" @click="confirmPending">确认</button><button @click="cancelPending">取消</button></view></view>
      <view v-if="imageContext" class="attachment"><image :src="resolveMediaUrl(imageContext.image_url)" /><text>图片已添加，可继续输入说明</text><button @click="imageContext=null">×</button></view>
      <view class="composer"><button class="image-btn" @click="chooseImage"><text class="button-label plus-label">＋</text></button><input v-model="text" :placeholder="pending || pendingLoan || pendingReimbursement ? '补充缺少的信息' : '午饭 28 元，或上传单据…'" confirm-type="send" @confirm="send()" /><button class="send" :disabled="busy" @click="send()"><text class="button-label">发送</text></button></view>
    </view>
  </view>
</template>

<style scoped>
.chat-page{height:100vh;display:flex;flex-direction:column;background:#f7f3ea}.chat-head{display:flex;justify-content:space-between;align-items:center;gap:20rpx;padding:22rpx 28rpx 18rpx;background:#fffaf1;border-bottom:1rpx solid #eee4d7}.head-copy{min-width:0}.chat-title{display:block;font-size:34rpx;font-weight:850}.ledger{display:block;max-width:310rpx;overflow:hidden;color:#91877a;font-size:22rpx;text-overflow:ellipsis;white-space:nowrap}.head-actions{display:flex;flex:none;align-items:center;gap:10rpx}.ledger-picker-button{display:flex;align-items:center;gap:7rpx;min-height:58rpx;padding:0 20rpx;border:1rpx solid #efd7c8;border-radius:18rpx;background:#fff3e8;color:#bd6243;font-size:23rpx;font-weight:700}.ledger-picker-button.disabled{opacity:.5}.chevron{margin-top:-5rpx;font-size:27rpx}.clear{min-height:58rpx;margin:0;padding:0 10rpx;background:transparent;color:#9a8d7d;font-size:24rpx;line-height:58rpx}.messages{box-sizing:border-box;flex:1;width:100%;height:0;padding:24rpx 30rpx}.welcome{text-align:center}.welcome text{display:block;margin:8rpx}.welcome .avatar{font-size:70rpx}.message-row{box-sizing:border-box;display:flex;width:100%;gap:14rpx;margin:22rpx 0;align-items:flex-start}.message-row.user{flex-direction:row-reverse;padding-right:14rpx}.mini-avatar{width:62rpx;height:62rpx;flex:none;display:flex;align-items:center;justify-content:center;border-radius:20rpx;background:#fff;font-weight:800;overflow:hidden}.mini-avatar image{width:100%;height:100%;object-fit:cover}.bubble{max-width:calc(100% - 90rpx);padding:20rpx 22rpx;border-radius:8rpx 24rpx 24rpx 24rpx;line-height:1.55;background:#fff}.bubble.user{background:#dc744d;color:#fff;border-radius:24rpx 8rpx 24rpx 24rpx}.document{display:block;width:360rpx;max-width:100%;height:240rpx;margin-bottom:14rpx;border-radius:16rpx}.parse{margin-top:18rpx;padding-top:16rpx;border-top:1rpx solid rgba(120,100,80,.15);font-size:23rpx}.parse-grid{display:grid;grid-template-columns:1fr 1fr;gap:10rpx;margin-top:10rpx;font-weight:700}.composer-wrap{padding:12rpx 20rpx calc(16rpx + env(safe-area-inset-bottom));background:#fffdf8;border-top:1rpx solid #eae1d5}.composer{display:flex;gap:12rpx;align-items:center}.composer input{flex:1;height:76rpx;padding:0 22rpx;background:#f5f0e8;border-radius:22rpx}.image-btn,.send{display:flex;flex:none;align-items:center;justify-content:center;height:76rpx;margin:0;line-height:1}.image-btn{width:76rpx;padding:0;background:#eee7dc;border-radius:22rpx;font-size:42rpx}.send{padding:0 24rpx;background:#dc744d;color:#fff;border-radius:22rpx;font-size:26rpx}.button-label{display:block;line-height:1;text-align:center}.plus-label{font-family:Arial,sans-serif}.pending,.attachment{display:flex;align-items:center;justify-content:space-between;padding:12rpx 16rpx;margin-bottom:10rpx;background:#fff3e6;border-radius:16rpx;color:#9b593e;font-size:23rpx}.pending view{display:flex}.pending button,.attachment button{margin:0;padding:0 12rpx;background:transparent;color:#c45f3e;font-size:23rpx}.attachment image{width:54rpx;height:54rpx;border-radius:10rpx}
.network-warning{padding:16rpx 24rpx;background:#fff0e8;color:#a44f39;font-size:23rpx;line-height:1.45}
/* 微信原生 tabBar 已包含底部安全区，避免输入栏重复抬高。 */
/* #ifdef MP-WEIXIN */
.composer-wrap{padding-bottom:16rpx}
/* #endif */
</style>


