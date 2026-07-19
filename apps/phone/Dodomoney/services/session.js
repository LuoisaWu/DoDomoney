import { reactive } from "vue";

function cachedSession() {
  try { return uni.getStorageSync("dodomoney-session") || {}; }
  catch { return {}; }
}

const cached = cachedSession();

export const session = reactive({
  ready: false,
  startupError: "",
  user: cached.user || null,
  ledgers: cached.ledgers || [],
  activeLedgerId: cached.activeLedgerId || null,
  persona: cached.persona || null
});

export function token() { return uni.getStorageSync("dodomoney-token") || ""; }
export function setLogin(data) {
  uni.setStorageSync("dodomoney-token", data.token);
  session.user = data.user;
  session.ledgers = data.ledgers || [];
  session.activeLedgerId = data.active_ledger_id || data.ledgers?.[0]?.id || null;
  session.startupError = "";
  persistSession();
}
export function persistSession() {
  uni.setStorageSync("dodomoney-session", { user: session.user, ledgers: session.ledgers, activeLedgerId: session.activeLedgerId, persona: session.persona });
}
export function clearLogin(expectedToken) {
  if (expectedToken && token() !== expectedToken) return false;
  uni.removeStorageSync("dodomoney-token");
  uni.removeStorageSync("dodomoney-session");
  Object.assign(session, { user: null, ledgers: [], activeLedgerId: null, persona: null, startupError: "" });
  return true;
}
export function requireLogin() {
  if (!session.user) {
    uni.reLaunch({ url: "/pages/auth/auth" });
    return false;
  }
  return true;
}
