import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The site is served from https://<user>.github.io/DQC/, so assets need this prefix.
export default defineConfig({
  base: "/DQC/",
  plugins: [react(), tailwindcss()],
  test: { environment: "jsdom" },
});
