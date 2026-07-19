import { createApp } from "vue";

import App from "./App.vue";
import { billBuddyLogo } from "./brandAssets";
import "./styles.css";
import "./sunshine-theme.css";

if (window.dodomoney) document.documentElement.classList.add("electron-shell");
const favicon = document.createElement("link");
favicon.rel = "icon";
favicon.href = billBuddyLogo;
document.head.appendChild(favicon);

createApp(App).mount("#root");
