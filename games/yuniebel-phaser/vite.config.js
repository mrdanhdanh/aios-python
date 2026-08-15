import { defineConfig } from "vite";

// base './' — chạy file:// lẫn GitHub Pages subpath (/games/yuniebel-phaser/dist/)
export default defineConfig({
  base: "./",
  server: { port: 5175, strictPort: true }, // tránh xung đột dashboard 5173 (P3-12)
  build: { outDir: "dist", emptyOutDir: true },
  test: {
    environment: "jsdom", // vitest — UMD vendor cần self (P2-2)
    include: ["test/**/*.test.js"] // CHỈ unit/integration; *.spec.js thuộc Playwright (tránh double-run)
  }
});
