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
  { name: "garden-day.png",     setup: (d) => { d.setPhase("G_INIT"); d.setPlayer(107, 70); d.freeze(true); d.setMessage("Yuniebel! Vào nhà đi!", 999); } },
  { name: "garden-dusk.png",    setup: (d) => { d.setPhase("G_CHASE"); d.setPlayer(153, 53); d.setDarkness(0.5); d.setButterfly(160, 43); d.freeze(true); } },
  { name: "garden-night.png",   setup: (d) => { d.setPhase("G_DARK"); d.setPlayer(133, 57); d.setDarkness(1); d.freeze(true); } },
  { name: "living.png",         setup: (d) => { d.setPhase("L_SEARCH"); d.setPlayer(107, 63); d.freeze(true); } },
  { name: "kitchen-blood.png",  setup: (d) => { d.setPhase("K_BLOOD"); d.setPlayer(73, 70); d.freeze(true); } },
  { name: "kitchen-choice.png", setup: (d) => { d.setPhase("K_CHOICE"); d.setPlayer(73, 70); d.freeze(true); } },
  { name: "haunted-ghost.png",  setup: (d) => { d.setPhase("H_INIT"); d.setPlayer(90, 63); d.freeze(true); } },
  { name: "haunted-block.png",  setup: (d) => { d.setPhase("H_BLOCK"); d.setPlayer(90, 63); d.freeze(true); } },
  { name: "hallway-scare1.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(50, 45); d.setScareZone(1); d.freeze(true); } },
  { name: "hallway-scare2.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(100, 45); d.setScareZone(2); d.freeze(true); } },
  { name: "hallway-scare3.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(153, 45); d.setScareZone(3); d.freeze(true); } },
  { name: "hallway-scare4.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(207, 45); d.setScareZone(4); d.freeze(true); } },
  { name: "hallway-scare5.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(263, 45); d.setScareZone(5); d.freeze(true); } },
  { name: "birthday.png",       setup: (d) => { d.setPhase("D_END"); d.setPlayer(80, 67); d.freeze(true); } },
  { name: "gameover.png",       setup: (d) => { d.setPhase("GAME_OVER"); d.freeze(true); } },
  { name: "end.png",            setup: (d) => { d.setPhase("END"); d.freeze(true); } },
];

// ===== TASK-079: pixel checks (AC-1/AC-4/AC-5/AC-10) =====
// Đếm pixel màu trong region canvas (PNG raw — locator.screenshot trả Buffer PNG, giải mã qua canvas)
function countPixelsInRegion(page, region, color) {
  return page.evaluate(({ region, color }) => {
    const c = document.getElementById("game");
    const ctx = c.getContext("2d");
    const d = ctx.getImageData(region.x, region.y, region.w, region.h).data;
    let n = 0;
    for (let i = 0; i < d.length; i += 4) {
      if (d[i] === color[0] && d[i + 1] === color[1] && d[i + 2] === color[2]) n++;
    }
    return n;
  }, { region, color });
}
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

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
    d.setPlayer(107, 63);
    d.freeze(true);
  });
  await page.waitForTimeout(100);
  const a = await page.locator("#game").screenshot();
  await page.waitForTimeout(500);
  const b = await page.locator("#game").screenshot();
  expect(Buffer.compare(a, b)).toBe(0);
});

test("TASK-079 AC-1: mèo hiển thị sau START tại spawn (pixel #f5a623 trong region)", async ({ page }) => {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForFunction(() => window.__yuniebel.getState().phase === "G_INIT");
  await page.waitForTimeout(500); // hết fade (0.35s)
  // spawn (107,70) logical → cam=30 → screen x=77 → canvas (231..279, 210..258)
  const n = await countPixelsInRegion(page, { x: 231, y: 210, w: 48, h: 48 }, hexToRgb("#f5a623"));
  expect(n).toBeGreaterThanOrEqual(30);
});

test("TASK-079 AC-4: nhà vẽ khớp wall — pixel wallCream/roofRed hiện khi cam=160 (player 300,50)", async ({ page }) => {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(500);
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("G_INIT");
    d.setPlayer(300, 50);
    d.freeze(true);
  });
  await page.waitForTimeout(100);
  // cam = min(300-77, 160) = 160 → nhà (267..320 logical) → screen 107..160 → canvas 321..480
  const wall = await countPixelsInRegion(page, { x: 321, y: 0, w: 159, h: 270 }, hexToRgb("#e8d9b8"));
  const roof = await countPixelsInRegion(page, { x: 321, y: 0, w: 159, h: 270 }, hexToRgb("#c0392b"));
  expect(wall).toBeGreaterThan(100);
  expect(roof).toBeGreaterThan(30);
});

test("TASK-079 AC-10: HALLWAY camera scroll — tường + scare5 skull hiện khi player 300,45", async ({ page }) => {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(500);
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("W_WALK");
    d.setPlayer(300, 45);
    d.setScareZone(5);
    d.freeze(true);
  });
  await page.waitForTimeout(100);
  // cam = min(300-77, 160) = 160 → tường #17131f phải hiện; skull #f4f6f8 tại screen 140 → canvas 420
  const wallN = await countPixelsInRegion(page, { x: 321, y: 0, w: 159, h: 270 }, hexToRgb("#17131f"));
  const skullN = await countPixelsInRegion(page, { x: 400, y: 60, w: 80, h: 90 }, hexToRgb("#f4f6f8"));
  expect(wallN).toBeGreaterThan(100);
  expect(skullN).toBeGreaterThan(10);
});

test("TASK-079 AC-5: mèo hiện diện trong các shot có player (pixel catBody)", async ({ page }) => {
  const cases = [
    { name: "garden-day", setup: "d.setPhase('G_INIT'); d.setPlayer(107,70); d.setMessage('Yuniebel! Vào nhà đi!',999);" },
    { name: "living", setup: "d.setPhase('L_SEARCH'); d.setPlayer(107,63);" },
    { name: "kitchen", setup: "d.setPhase('K_BLOOD'); d.setPlayer(73,70);" },
    { name: "haunted", setup: "d.setPhase('H_INIT'); d.setPlayer(90,63);" },
    { name: "hallway", setup: "d.setPhase('W_WALK'); d.setPlayer(100,45);" },
    { name: "birthday", setup: "d.setPhase('D_END'); d.setPlayer(80,67);" },
  ];
  for (const c of cases) {
    await page.goto(URL);
    await page.click("#btn-start");
    await page.waitForTimeout(500);
    await page.evaluate((setup) => {
      const d = window.__yuniebel.debug;
      eval(setup);
      d.freeze(true);
    }, c.setup);
    await page.waitForTimeout(100);
    const n = await countPixelsInRegion(page, { x: 0, y: 0, w: 480, h: 270 }, hexToRgb("#f5a623"));
    expect(n, c.name + " phải có mèo").toBeGreaterThan(30);
  }
});

test("AC-12: COMPARISON.md tồn tại và có bảng đối chiếu", async ({ page }) => {
  const cmpPath = path.join(BRIEF, "COMPARISON.md");
  expect(fs.existsSync(cmpPath)).toBeTruthy();
  const content = fs.readFileSync(cmpPath, "utf8");
  expect(content).toContain("## Kết luận");
  expect(content).toContain("17/17");
});
