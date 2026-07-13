import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  // Electron loads the production renderer through file://, so assets must
  // be referenced relative to dist/renderer/index.html instead of /assets.
  base: "./",
  server: {
    port: 5173
  },
  build: {
    outDir: "dist/renderer"
  }
});
