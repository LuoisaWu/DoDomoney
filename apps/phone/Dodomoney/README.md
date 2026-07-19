# Dodomoney 手机端

基于 uni-app + Vue 3，与 `apps/api` 和桌面端共享账户、账本、账单及助手数据。

## H5 开发

```powershell
npm.cmd install
npm.cmd run dev:h5
```

构建验证：

```powershell
npm.cmd run build:h5
```

也可以直接用 HBuilderX 打开当前 `Dodomoney` 文件夹并运行到浏览器、模拟器或真机。

## 微信小程序

条件编译标识使用 `MP-WEIXIN`。App、H5 和微信小程序共享页面与业务服务，仅将微信更新管理器、图片选择和小程序 API 地址编译进微信端。

开发和构建：

```powershell
npm.cmd run dev:mp-weixin
npm.cmd run build:mp-weixin
```

构建产物位于 `dist/build/mp-weixin`，使用微信开发者工具导入该目录即可。正式发布前还需要：

1. 在 `manifest.json` 的 `mp-weixin.appid` 填入小程序 AppID。
2. 复制 `.env.example` 为 `.env.local`，填写 `VITE_MP_API_BASE_URL`。
3. 在微信公众平台把 API 域名同时加入 `request` 和 `uploadFile` 合法域名。
4. API 使用已备案的 HTTPS 域名；微信开发者工具里的“不校验合法域名”只适用于本地开发。
5. 在微信公众平台补充用户隐私保护指引，说明头像和单据图片的使用目的。

## 后端地址

默认地址是 `http://127.0.0.1:8000`。在真机上，`127.0.0.1` 指手机本身，需要在项目目录创建 `.env.local`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_APP_API_BASE_URL=http://你的电脑局域网IP:8000
```

Android USB 真机调试推荐在项目根目录双击 `start-phone-debug.bat`。它会使用 HBuilderX 的 ADB 建立端口反向代理：

```text
手机 127.0.0.1:8000 → USB → 电脑 127.0.0.1:8000
```

然后在 App 登录页点击“使用 USB 调试”，服务地址会切换为 `http://127.0.0.1:8000`。这种方式不依赖 Wi-Fi，也不会受电脑局域网 IP 变化影响。

无线调试时，可以直接在 App 登录页把“后端服务地址”改为电脑的 WLAN IPv4，例如 `http://192.168.1.10:8000`。

如果电脑连接的是手机热点，推荐双击项目根目录的 `start-phone-wifi-debug.bat`。脚本会自动：

- 识别当前默认网络对应的电脑 IPv4；
- 更新 `.env.local` 中的 `VITE_APP_API_BASE_URL`；
- 检查并启动 API；
- 输出登录页应使用的完整地址。

脚本执行后需要在 HBuilderX 中重新运行一次项目到手机，使新的 `.env.local` 进入调试包，然后点击登录页的“使用热点调试”。

`start-api.bat` 已让 API 监听 `0.0.0.0:8000`。请确保手机和电脑在同一网络、防火墙允许访问 8000 端口。生产包应使用 HTTPS API 地址。

如果登录后短暂进入首页又返回登录页，先在手机中删除旧的 HBuilder 调试基座应用数据，再重新运行。当前代码只会在后端明确返回 401/403 时清除会话，普通断网不会再清除刚完成的登录。

## 功能

- 邮箱验证码注册、登录、会话恢复和退出
- AI 对话记账、上下文追问、借款/报销确认、单据图片识别
- 账单查看、编辑和删除
- 区间收支分析、AI 解读、分类占比、借还款拆分和月预算
- 借款增删改、等额本息/等额本金还款计划
- 发票报销全流程状态管理
- 年度综合所得税测算
- 多账本切换、创建账本和添加成员
- 用户头像、助手头像、人格、语气、回复长度及专属要求
