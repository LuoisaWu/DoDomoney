import { contextBridge } from "electron";

contextBridge.exposeInMainWorld("dodomoney", {
  platform: process.platform,
  appName: "Dodomoney"
});
