# Dodomoney Desktop

Electron + Vue 3 + TypeScript 桌面客户端。

## 运行

```powershell
npm install
npm run dev
```

桌面端依赖后端 `http://127.0.0.1:8000`。如需修改地址，可在 `apps/desktop/.env` 中设置 `VITE_API_BASE_URL`。

## 目录

- `src/main`：Electron 主进程。
- `src/preload`：安全桥接层。
- `src/renderer`：Vue 3 页面、组件、接口调用。
