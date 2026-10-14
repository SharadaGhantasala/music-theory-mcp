import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development the backend runs separately, so API calls are proxied to it.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
