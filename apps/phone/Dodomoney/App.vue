<script>
import { api } from "./services/api";
import { clearLogin, persistSession, session, setLogin, token } from "./services/session";
export default {
  async onLaunch() {
    // 微信小程序使用自身的热更新管理器；App/H5 不会编译这段代码。
    // #ifdef MP-WEIXIN
    const updateManager = uni.getUpdateManager();
    updateManager.onUpdateReady(() => uni.showModal({
      title: "发现新版本",
      content: "新版本已准备好，是否立即重启？",
      success: result => { if (result.confirm) updateManager.applyUpdate(); }
    }));
    // #endif
    const restoringToken = token();
    if (!restoringToken) { session.ready = true; return; }
    try {
      const data = await api.restore();
      if (token() !== restoringToken) return;
      setLogin({ ...data, token: restoringToken });
      session.persona = await api.persona();
      persistSession();
    } catch (error) {
      if (token() !== restoringToken) return;
      if (error?.statusCode === 401 || error?.statusCode === 403) {
        clearLogin(restoringToken);
      } else {
        session.startupError = error?.message || "暂时无法连接后端，已保留本地登录状态";
      }
    }
    finally { session.ready = true; }
  }
};
</script>

<style>
page { background: #f7f3ea; color: #302d29; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 28rpx; }
view, text, input, textarea, button, picker { box-sizing: border-box; }
button::after { border: 0; }
.page { min-height: 100vh; padding: 28rpx 28rpx calc(40rpx + env(safe-area-inset-bottom)); }
.hero { padding: 18rpx 4rpx 28rpx; }
.eyebrow { color: #dc744d; font-size: 22rpx; font-weight: 700; letter-spacing: 2rpx; }
.title { display: block; margin-top: 8rpx; font-size: 42rpx; line-height: 1.25; font-weight: 800; }
.subtle { display: block; margin-top: 10rpx; color: #827a70; line-height: 1.55; }
.card { margin-bottom: 22rpx; padding: 28rpx; background: #fffdf8; border: 1rpx solid #ebe2d5; border-radius: 28rpx; box-shadow: 0 10rpx 30rpx rgba(91,70,41,.06); }
.card-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22rpx; font-weight: 750; font-size: 31rpx; }
.muted { color: #91877a; font-size: 24rpx; }
.btn { display: flex; align-items: center; justify-content: center; min-height: 82rpx; padding: 0 30rpx; border-radius: 22rpx; font-size: 28rpx; font-weight: 700; background: #efe9df; color: #514c45; }
.btn.primary { background: #dc744d; color: white; }
.btn.danger { color: #b34b42; background: #fff0ec; }
.btn.small { display: inline-flex; min-height: 58rpx; padding: 0 22rpx; border-radius: 16rpx; font-size: 24rpx; }
.btn[disabled] { opacity: .5; }
.input, .textarea, .picker { width: 100%; min-height: 82rpx; margin-top: 12rpx; padding: 0 24rpx; color: #302d29; background: #faf7f1; border: 1rpx solid #e5ddd1; border-radius: 20rpx; }
.textarea { height: 170rpx; padding-top: 20rpx; }
.field { display: block; margin-bottom: 22rpx; color: #696259; font-size: 25rpx; font-weight: 650; }
.row { display: flex; align-items: center; gap: 16rpx; }
.between { justify-content: space-between; }
.money { font-variant-numeric: tabular-nums; font-weight: 800; }
.strong { font-weight: 800; }
.income { color: #45966d; }.expense { color: #d86a48; }
.metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 18rpx; margin-bottom: 22rpx; }
.metric { padding: 24rpx; background: #fffdf8; border: 1rpx solid #ebe2d5; border-radius: 24rpx; }
.metric text { display: block; color: #8b8174; font-size: 23rpx; }.metric .strong { display: block; margin-top: 10rpx; font-size: 34rpx; }
.empty { padding: 60rpx 20rpx; text-align: center; color: #93897c; line-height: 1.7; }
.sheet-mask { position: fixed; inset: 0; z-index: 50; display: flex; align-items: flex-end; background: rgba(39,33,26,.45); }
.sheet { width: 100%; max-height: 90vh; overflow-y: auto; padding: 34rpx 28rpx calc(34rpx + env(safe-area-inset-bottom)); background: #fffdf8; border-radius: 36rpx 36rpx 0 0; }
.sheet-head { display: flex; justify-content: space-between; margin-bottom: 28rpx; font-size: 34rpx; font-weight: 800; }
.pill { display: inline-flex; padding: 8rpx 16rpx; border-radius: 99rpx; background: #f0ece5; color: #766e63; font-size: 22rpx; }
</style>


