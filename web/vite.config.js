import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api -> FastAPI (8000), so the UI can fetch("/api/...")
// with no CORS dance and the same code works if ever served behind one host.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
