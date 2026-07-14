import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// In dev, proxy API calls to the local backend so the SPA and API share an origin.
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/v1": "http://localhost:8080",
      "/health": "http://localhost:8080",
    },
  },
});
