/* playwright.config.js — TASK-078
 * R10: testMatch e2e + visual; timeout dài cho AC-14; autoplay policy cho headless.
 */
const config = {
  testDir: "./test",
  testMatch: /(e2e|visual)\.spec\.js/,
  timeout: 120000, // R3: AC-14 chơi thật 40–90s
  retries: 0,
  use: {
    baseURL: "file://" + __dirname.replace(/\\/g, "/") + "/index.html",
    headless: true,
    viewport: { width: 640, height: 480 },
    launchOptions: {
      args: ["--autoplay-policy=no-user-gesture-required"] // R2
    }
  },
  webServer: null, // file:// works
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
  ],
};
module.exports = config;
