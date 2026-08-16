import { defineConfig } from "@playwright/test";

// TASK-081 — webServer: build trước rồi preview (Vite module script không chạy file:// — P2-8)
export default defineConfig({
  testDir: "./test",
  testMatch: /(e2e|visual)\.spec\.js/,
  timeout: 120000, // AC-4/AC-5: chơi thật 40–90s (P3-5)
  retries: 0,
  use: {
    baseURL: "http://localhost:4174",
    headless: true,
    viewport: { width: 480, height: 270 }, // khớp canvas → screenshot element = 480×270
    launchOptions: {
      args: ["--autoplay-policy=no-user-gesture-required"] // P3-8: audio mood e2e
    }
  },
  webServer: {
    command: "npm run build && npm run preview -- --port 4174 --strictPort",
    url: "http://localhost:4174",
    timeout: 120000,
    reuseExistingServer: !process.env.CI
  },
  projects: [
    { name: "chromium", use: { browserName: "chromium" } }
  ]
});
