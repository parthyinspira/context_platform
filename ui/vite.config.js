import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
  },
  test: {
    environment: "jsdom",
    include: ["test/**/*.test.{js,jsx}"],
    setupFiles: ["./test/setup.js"],
  },
});
