import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
  },
  resolve: {
    alias: {
      "@codemirror/state": resolve(__dirname, "node_modules/@codemirror/state"),
      "@codemirror/view": resolve(__dirname, "node_modules/@codemirror/view"),
    },
  },
});