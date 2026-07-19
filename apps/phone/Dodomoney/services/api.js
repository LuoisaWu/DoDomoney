import { session, token } from "./session";

let API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
let APP_CONFIGURED_API_BASE_URL = import.meta.env.VITE_APP_API_BASE_URL || "http://10.128.117.85:8000";

// App 真机中的 127.0.0.1 是手机本身，开发时应使用电脑的局域网地址。
// 使用 scripts/start-phone-debug.bat 建立 ADB reverse 后，127.0.0.1:8000 会通过 USB 转发到电脑。
// #ifdef APP-PLUS
API_BASE_URL = APP_CONFIGURED_API_BASE_URL;
// #endif

// 微信小程序真机必须使用已加入 request/uploadFile 合法域名的 HTTPS 地址。
// #ifdef MP-WEIXIN
API_BASE_URL = import.meta.env.VITE_MP_API_BASE_URL || import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
// #endif

const savedApiBaseUrl = uni.getStorageSync("dodomoney-api-base-url");
if (savedApiBaseUrl) API_BASE_URL = savedApiBaseUrl;

export function getApiBaseUrl() { return API_BASE_URL; }
export function getConfiguredAppApiBaseUrl() { return APP_CONFIGURED_API_BASE_URL; }
export function resolveMediaUrl(value) {
  if (!value || /^data:image\//i.test(value)) return value || "";
  const mediaIndex = value.indexOf("/media/");
  if (mediaIndex >= 0) return `${API_BASE_URL}${value.slice(mediaIndex)}`;
  return value;
}
export function setApiBaseUrl(value) {
  const normalized = String(value || "").trim().replace(/\/+$/, "");
  if (!/^https?:\/\/[^/\s]+(?::\d+)?$/i.test(normalized)) {
    throw new Error("服务地址格式不正确，例如：http://192.168.1.10:8000");
  }
  API_BASE_URL = normalized;
  uni.setStorageSync("dodomoney-api-base-url", normalized);
  return API_BASE_URL;
}

class ApiError extends Error {
  constructor(message, statusCode = 0) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

function headers(json = true) {
  const value = {};
  if (json) value["Content-Type"] = "application/json";
  if (token()) value.Authorization = `Bearer ${token()}`;
  if (session.user?.id) value["X-Dodomoney-User-Id"] = String(session.user.id);
  if (session.activeLedgerId) value["X-Dodomoney-Ledger-Id"] = String(session.activeLedgerId);
  return value;
}

function request(path, method = "GET", data) {
  return new Promise((resolve, reject) => uni.request({
    url: `${API_BASE_URL}${path}`, method, data, header: headers(),
    success(response) {
      if (response.statusCode >= 200 && response.statusCode < 300) resolve(response.data);
      else reject(new ApiError(response.data?.detail || `请求失败 (${response.statusCode})`, response.statusCode));
    },
    fail(error) {
      reject(new ApiError(
        `${error.errMsg || "网络请求失败"}。当前服务地址：${API_BASE_URL}`,
        0
      ));
    }
  }));
}

function upload(path, filePath) {
  return new Promise((resolve, reject) => uni.uploadFile({
    url: `${API_BASE_URL}${path}`, filePath, name: "file", header: headers(false),
    success(response) {
      let data; try { data = JSON.parse(response.data); } catch { data = {}; }
      if (response.statusCode >= 200 && response.statusCode < 300) resolve(data);
      else reject(new Error(data.detail || `上传失败 (${response.statusCode})`));
    },
    fail(error) { reject(new Error(error.errMsg || "上传失败")); }
  }));
}

export const api = {
  sendCode: email => request("/auth/verification-code", "POST", { email }),
  login: (email, password) => request("/auth/login", "POST", { email, password }),
  register: (email, display_name, password, verification_code) => request("/auth/register", "POST", { email, display_name, password, verification_code }),
  restore: () => request("/auth/session"), logout: () => request("/auth/logout", "POST"),
  listEntries: () => request("/entries"),
  updateEntry: (id, data) => request(`/entries/${id}`, "PATCH", data),
  deleteEntry: id => request(`/entries/${id}`, "DELETE"),
  messages: () => request("/chat/messages"), clearMessages: () => request("/chat/messages", "DELETE"),
  record: (message, pending_context, pending_loan, pending_reimbursement, image_context) => request("/chat/record", "POST", { message, pending_context, pending_loan, pending_reimbursement, image_context }),
  uploadDocument: path => upload("/uploads/document-ocr?analyze=false", path), uploadAvatar: path => upload("/uploads/avatar", path),
  analyze: (start, end, ai = false) => request(`/entries/analysis?start_date=${start}&end_date=${end}&include_ai=${ai}`),
  budgets: () => request("/budgets"), createBudget: (month, amount, category) => request("/budgets", "POST", { month: `${month}-01`, amount, category: category || null }), deleteBudget: id => request(`/budgets/${id}`, "DELETE"),
  loans: () => request("/loans"), createLoan: data => request("/loans", "POST", data), updateLoan: (id, data) => request(`/loans/${id}`, "PATCH", data), deleteLoan: id => request(`/loans/${id}`, "DELETE"),
  reimbursements: () => request("/reimbursements"), createReimbursement: data => request("/reimbursements", "POST", data), updateReimbursement: (id, data) => request(`/reimbursements/${id}`, "PATCH", data), deleteReimbursement: id => request(`/reimbursements/${id}`, "DELETE"),
  persona: () => request("/users/me/persona"), updatePersona: data => request("/users/me/persona", "PUT", data), updateUser: data => request("/users/me", "PATCH", data),
  ledgers: () => request("/ledgers"), createLedger: (name, type) => request("/ledgers", "POST", { name, type }), members: id => request(`/ledgers/${id}/members`), addMember: (id, email, display_name) => request(`/ledgers/${id}/members`, "POST", { email, display_name: display_name || null, role: "member" })
};

export function showError(error, fallback = "操作失败") { uni.showToast({ title: error?.message || fallback, icon: "none", duration: 2600 }); }
