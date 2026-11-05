import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The GitHub Pages base path is added in the deploy slice.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: { environment: "jsdom" },
});
