/* visual.spec.js — TASK-081 (bản Phaser) — npx playwright test visual
 * AC-6 (P2-B3): mỗi shot = goto → START → chờ ≥500ms (fade hết) → setter → freeze(true)
 * → chờ ≥100ms → chụp lần 1 → chờ 500ms → chụp lần 2 so khớp (determinism).
 * Ảnh lưu test-results/shots/; đối chiếu thủ công trong test/brief/COMPARISON.md vs refs/1..6.png
 * (nguồn chuẩn: aios/progress/tasks/TASK-078/implementation/brief-visuals.md — P3-B4).
 * KHÔNG dùng getImageData (WebGL — P1-2): kiểm chứng = screenshot compositor + freeze determinism.
 */
import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const URL = "/?test=1";
const OUT = path.join(__dirname, "..", "test-results", "shots");
const BRIEF = path.join(__dirname, "brief");

const SHOTS = [
  // ===== 7 ảnh chính (AC-6) =====
  { name: "title.png",          setup: (d) => { d.setPhase("TITLE"); d.freeze(true); } },
  { name: "garden-day.png",     setup: (d) => { d.setPhase("G_INIT"); d.setPlayer(107, 70); d.freeze(true); d.setMessage("Yuniebel! Vào nhà đi!", 999); } },
  { name: "living.png",         setup: (d) => { d.setPhase("L_SEARCH"); d.setPlayer(107, 63); d.freeze(true); } },
  { name: "kitchen-blood.png",  setup: (d) => { d.setPhase("K_BLOOD"); d.setPlayer(73, 70); d.freeze(true); } },
  { name: "haunted-ghost.png",  setup: (d) => { d.setPhase("H_INIT"); d.setPlayer(90, 63); d.freeze(true); } },
  { name: "hallway-scare1.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(50, 45); d.setScareZone(1); d.freeze(true); } },
  { name: "birthday.png",       setup: (d) => { d.setPhase("D_END"); d.setPlayer(80, 67); d.freeze(true); } },
  // ===== 5 ảnh phụ hallway-scare2..5 (AC-10) =====
  { name: "hallway-scare2.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(100, 45); d.setScareZone(2); d.freeze(true); } },
  { name: "hallway-scare3.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(153, 45); d.setScareZone(3); d.freeze(true); } },
  { name: "hallway-scare4.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(207, 45); d.setScareZone(4); d.freeze(true); } },
  { name: "hallway-scare5.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(263, 45); d.setScareZone(5); d.freeze(true); } },
  // ===== bổ sung (parity vanilla) =====
  { name: "garden-dusk.png",    setup: (d) => { d.setPhase("G_CHASE"); d.setPlayer(153, 53); d.setDarkness(0.5); d.setButterfly(160, 43); d.freeze(true); } },
  { name: "garden-night.png",   setup: (d) => { d.setPhase("G_DARK"); d.setPlayer(133, 57); d.setDarkness(1); d.freeze(true); } },
  { name: "kitchen-choice.png", setup: (d) => { d.setPhase("K_CHOICE"); d.setPlayer(73, 70); d.freeze(true); } },
  { name: "haunted-block.png",  setup: (d) => { d.setPhase("H_BLOCK"); d.setPlayer(90, 63); d.freeze(true); } },
  { name: "gameover.png",       setup: (d) => { d.setPhase("GAME_OVER"); d.freeze(true); } },
  { name: "end.png",            setup: (d) => { d.setPhase("END"); d.freeze(true); } },
];

test.describe("visual screenshots (AC-6/AC-10)", () => {
  test.beforeAll(async () => {
    fs.mkdirSync(OUT, { recursive: true });
  });

  for (const shot of SHOTS) {
    test("chụp " + shot.name, async ({ page }) => {
      await page.goto(URL);
      await page.click("#btn-start");
      await page.waitForTimeout(500); // P2-B3: chờ fade 0.35s hết trước khi freeze
      await page.evaluate((setup) => {
        const d = window.__yuniebel.debug;
        eval(setup);
      }, "(" + shot.setup.toString() + ")(window.__yuniebel.debug)");
      await page.waitForTimeout(100); // render 1 frame sau freeze
      const img1 = await page.locator("#game").screenshot();
      fs.writeFileSync(path.join(OUT, shot.name), img1);
      expect(img1.length).toBeGreaterThan(1000); // ảnh không rỗng
      // determinism: ảnh lần 2 cách 500ms phải giống hệt (R1)
      await page.waitForTimeout(500);
      const img2 = await page.locator("#game").screenshot();
      expect(Buffer.compare(img1, img2)).toBe(0);
    });
  }
});

test("R1: freeze determinism riêng — 2 ảnh cách 500ms giống hệt (L_SEARCH)", async ({ page }) => {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(500);
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("L_SEARCH");
    d.setPlayer(107, 63);
    d.freeze(true);
  });
  await page.waitForTimeout(100);
  const a = await page.locator("#game").screenshot();
  await page.waitForTimeout(500);
  const b = await page.locator("#game").screenshot();
  expect(Buffer.compare(a, b)).toBe(0);
});

test("AC-7b: camX expose — camera scroll khớp công thức vanilla (HALLWAY)", async ({ page }) => {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(500);
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("W_WALK");
    d.setPlayer(20, 45);
    d.freeze(true);
  });
  await page.waitForTimeout(100);
  let cx = await page.evaluate(() => window.__yuniebel.camX());
  expect(cx).toBe(0); // player 20 ≤ 77
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPlayer(300, 45);
  });
  await page.waitForTimeout(100);
  cx = await page.evaluate(() => window.__yuniebel.camX());
  expect(cx).toBe(160); // min(300-77, 320-160) = 160 (HALLWAY w=320)
});
