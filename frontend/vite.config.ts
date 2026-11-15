import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

declare const process: { env: Record<string, string | undefined> }; // Node global (no @types/node in this project)

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // API_URL lets a second dev stack run beside one that already holds :8000 (e.g. API_URL=http://127.0.0.1:8001).
    proxy: { "/api": process.env.API_URL ?? "http://127.0.0.1:8000" },
  },
});
