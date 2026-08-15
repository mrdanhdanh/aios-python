/* visual.spec.js — TASK-078 — npx playwright test
 * AC-11: chụp 17 ảnh theo bảng §8.1 bằng locator('canvas').screenshot()
 * (clip đúng canvas 480×270 — C2-13). Ảnh lưu test-results/shots/.
 * R1: test freeze determinism (chụp 2 lần với freeze → pixel giống hệt).
 */
const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const URL = "file://" + __dirname.replace(/\\/g, "/") + "/../index.html?test=1";
const OUT = path.join(__dirname, "..", "test-results", "shots");
const BRIEF = path.join(__dirname, "brief");

const SHOTS = [
  { name: "title.png",          setup: (d) => { d.setPhase("TITLE"); d.freeze(true); } },
  { name: "garden-day.png",     setup: (d) => { d.setPhase("G_INIT"); d.setPlayer(320, 210); d.freeze(true); d.setMessage("Yuniebel! Vào nhà đi!", 999); } },
  { name: "garden-dusk.png",    setup: (d) => { d.setPhase("G_CHASE"); d.setPlayer(460, 160); d.setDarkness(0.5); d.setButterfly(480, 130); d.freeze(true); } },
  { name: "garden-night.png",   setup: (d) => { d.setPhase("G_DARK"); d.setPlayer(400, 170); d.setDarkness(1); d.freeze(true); } },
  { name: "living.png",         setup: (d) => { d.setPhase("L_SEARCH"); d.setPlayer(320, 190); d.freeze(true); } },
  { name: "kitchen-blood.png",  setup: (d) => { d.setPhase("K_BLOOD"); d.setPlayer(220, 230); d.freeze(true); } },
  { name: "kitchen-choice.png", setup: (d) => { d.setPhase("K_CHOICE"); d.setPlayer(220, 230); d.freeze(true); } },
  { name: "haunted-ghost.png",  setup: (d) => { d.setPhase("H_INIT"); d.setPlayer(240, 190); d.freeze(true); } },
  { name: "haunted-block.png",  setup: (d) => { d.setPhase("H_BLOCK"); d.setPlayer(240, 190); d.freeze(true); } },
  { name: "hallway-scare1.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(150, 135); d.setScareZone(1); d.freeze(true); } },
  { name: "hallway-scare2.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(300, 135); d.setScareZone(2); d.freeze(true); } },
  { name: "hallway-scare3.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(460, 135); d.setScareZone(3); d.freeze(true); } },
  { name: "hallway-scare4.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(620, 135); d.setScareZone(4); d.freeze(true); } },
  { name: "hallway-scare5.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(790, 135); d.setScareZone(5); d.freeze(true); } },
  { name: "birthday.png",       setup: (d) => { d.setPhase("D_END"); d.setPlayer(240, 200); d.freeze(true); } },
  { name: "gameover.png",       setup: (d) => { d.setPhase("GAME_OVER"); d.freeze(true); } },
  { name: "end.png",            setup: (d) => { d.setPhase("END"); d.freeze(true); } },
];

test.describe("visual screenshots (AC-11)", () => {
  test.beforeAll(async ({ browser }) => {
    fs.mkdirSync(OUT, { recursive: true });
  });

  for (const shot of SHOTS) {
    test("chụp " + shot.name, async ({ page }) => {
      await page.goto(URL);
      await page.click("#btn-start");
      await page.waitForTimeout(500); // chờ fade chuyển cảnh hết (fadeT 0.35s)
      await page.evaluate((setup) => {
        const d = window.__yuniebel.debug;
        eval(setup);
      }, "(" + shot.setup.toString() + ")(window.__yuniebel.debug)");
      await page.waitForTimeout(100); // để render 1 frame
      const img = await page.locator("#game").screenshot();
      fs.writeFileSync(path.join(OUT, shot.name), img);
      expect(img.length).toBeGreaterThan(1000); // ảnh không rỗng
      // so sánh với ảnh ref nếu có (AC-12: skip khi thiếu ref)
      const ref = path.join(BRIEF, shot.name);
      if (fs.existsSync(ref)) {
        await expect(page.locator("#game")).toHaveScreenshot(shot.name, { maxDiffPixelRatio: 0.02 });
      }
    });
  }
});

test("R1: freeze determinism — 2 ảnh cách 500ms giống hệt", async ({ page }) => {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(500); // chờ fade hết
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("L_SEARCH");
    d.setPlayer(320, 190);
    d.freeze(true);
  });
  await page.waitForTimeout(100);
  const a = await page.locator("#game").screenshot();
  await page.waitForTimeout(500);
  const b = await page.locator("#game").screenshot();
  expect(Buffer.compare(a, b)).toBe(0);
});

test("AC-12: COMPARISON.md tồn tại và có bảng đối chiếu", async ({ page }) => {
  const cmpPath = path.join(BRIEF, "COMPARISON.md");
  expect(fs.existsSync(cmpPath)).toBeTruthy();
  const content = fs.readFileSync(cmpPath, "utf8");
  expect(content).toContain("## Kết luận");
  expect(content).toContain("17/17");
});
