import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  esbuild: {
    jsx: "automatic",
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
  define: {
    "process.env.NEXT_PUBLIC_API_KEY": JSON.stringify("test-api-key"),
    "process.env.NEXT_PUBLIC_API_URL": JSON.stringify("http://localhost:8000"),
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
  },
});