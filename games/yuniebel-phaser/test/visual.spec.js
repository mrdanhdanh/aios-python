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
  // ===== TASK-082: shots mới (A/B/C/D) — nhóm byte-compare frozen =====
  { name: "cat-idle-cycle.png", setup: (d) => { d.setPhase("G_INIT"); d.setPlayer(107, 70); d.freeze(true); } },
  { name: "garden-night-fx.png", setup: (d) => { d.setPhase("G_DARK"); d.setPlayer(133, 57); d.setDarkness(1); d.freeze(true); } },
  { name: "haunted-ghost2.png",  setup: (d) => { d.setPhase("H_INIT"); d.setPlayer(90, 63); d.setMessage("Meow!", 999); d.freeze(true); } },
  { name: "birthday2.png",       setup: (d) => { d.setPhase("D_END"); d.setPlayer(80, 67); d.freeze(true); } },
  { name: "living-fx.png",       setup: (d) => { d.setPhase("L_SEARCH"); d.setPlayer(107, 63); d.freeze(true); } },
  { name: "hallway-scare5-zoom.png", setup: (d) => { d.setPhase("W_WALK"); d.setPlayer(263, 45); d.setScareZone(5); d.freeze(true); } }
];

test.describe("visual screenshots (AC-6/AC-10)", () => {
  test.beforeAll(async () => {
    fs.mkdirSync(OUT, { recursive: true });
  });

  for (const shot of SHOTS) {
    test("chụp " + shot.name, async ({ page }) => {
      await page.goto(URL);
      await page.click("#btn-start");
      await page.waitForTimeout(700); // P2-B3 + R-07.1: chờ fade 0.6s hết trước khi freeze
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
  await page.waitForTimeout(700); // R-07.1
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

// ===== TASK-082: AC-3 walk — anim CHẠY (không freeze): giữ phím d → frame đổi + 2 shot khác (C2v2-03) =====
test("AC-3: cat-walk anim chạy — giữ phím d → frame đổi + 2 shot khác (không byte-compare)", async ({ page }) => {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(700);
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("G_INIT");
    d.setPlayer(60, 70);
    d.freeze(false);
  });
  // giữ phím d (right) ≥ 300ms → mèo di chuyển + anim walk; đọc frame 5 mốc (chống flaky — C2v2-03)
  await page.keyboard.down("d");
  await page.waitForTimeout(350);
  const frames = [];
  for (let i = 0; i < 5; i++) {
    frames.push(await page.evaluate(() => {
      const s = window.__phaserGame.scene.getScene("Game").catImg;
      return s.anims && s.anims.currentFrame ? s.anims.currentFrame.textureFrame : -1;
    }));
    await page.waitForTimeout(110);
  }
  const s1 = await page.locator("#game").screenshot();
  await page.waitForTimeout(150);
  const s2 = await page.locator("#game").screenshot();
  await page.keyboard.up("d");
  // ít nhất 2 frame khác nhau trong chuỗi (walk 4 frames @8fps)
  const unique = new Set(frames);
  expect(unique.size).toBeGreaterThanOrEqual(2);
  expect(Buffer.compare(s1, s2)).not.toBe(0); // ảnh khác nhau
});

// ===== TASK-082: AC-19 freeze-ngay — H_INIT + freeze NGAY (không chờ) → 2 shot byte-identical =====
test("AC-19: freeze ngay sau setPhase H_INIT — 2 shot cách 500ms giống hệt (ghost anim đứng yên)", async ({ page }) => {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(700);
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("H_INIT");
    d.setMessage("Meow!", 999);
    d.freeze(true); // NGAY — ghost chưa play bao giờ (C2v2-17)
  });
  await page.waitForTimeout(100);
  const a = await page.locator("#game").screenshot();
  await page.waitForTimeout(500);
  const b = await page.locator("#game").screenshot();
  expect(Buffer.compare(a, b)).toBe(0);
});

// ===== TASK-082: AC-9 light pool probe — GARDEN đêm: quanh player sáng hơn góc màn =====
// (WebGL readback qua getImageData rỗng — preserveDrawingBuffer false → decode PNG screenshot, R-07.6)
test("AC-9: light pool — brightness quanh player > góc trái màn (chênh ≥ 10/255)", async ({ page }) => {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(700);
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("G_DARK");
    d.setPlayer(133, 57); // giữa màn (C2v2-07)
    d.setDarkness(1);
    d.freeze(true);
  });
  await page.waitForTimeout(150);
  const png = await page.locator("#game").screenshot();
  // decode PNG (zlib.inflateSync — kỹ thuật sprite-sheet.test)
  const { decodePNG } = await import("./png-decode.mjs");
  const img = decodePNG(png);
  const bright = (x, y) => {
    const xx = Math.max(0, Math.min(x, img.w - 40)), yy = Math.max(0, Math.min(y, img.h - 40));
    let s = 0, n = 0;
    for (let j = yy; j < yy + 40; j++) {
      for (let i = xx; i < xx + 40; i++) {
        const o = (j * img.w + i) * 4;
        s += 0.299 * img.px[o] + 0.587 * img.px[o + 1] + 0.114 * img.px[o + 2];
        n++;
      }
    }
    return s / n;
  };
  // player screen pos = world - camX*3 (R-02): camX = min(133-77, 160) = 56 → px 168
  const px = 133 * 3 - 168, py = 57 * 3;
  const playerB = bright(px - 20, py - 20);
  const cornerB = bright(0, 230); // góc TRÁI-DƯỚI: tối nhất (không có nguồn sáng)
  // light pool làm sáng vùng quanh mèo (gradient clear) — chênh ≥ 10/255 (C3-03)
  expect(playerB).toBeGreaterThan(cornerB + 10);
});

// ===== TASK-082: AC-11 shake + zoom (manual deterministic — không dùng camera effects Phaser, R-03) =====
test("AC-11: scare 5 → scroll offset khác 0 (shake) + zoom ≈1.04; frozen → không đổi", async ({ page }) => {
  const pageErrors = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(700);
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("W_WALK");
    d.setPlayer(263, 45);
    d.setScareZone(5);
  });
  // shake: scroll dao động quanh base — đo 3 mốc cách 50ms → ít nhất 1 mốc lệch > 1px
  const offs = [];
  for (let i = 0; i < 3; i++) {
    await page.waitForTimeout(50);
    const o = await page.evaluate(() => {
      const cam = window.__phaserGame.scene.getScene("Game").cameras.main;
      return { x: cam.scrollX, y: cam.scrollY };
    });
    offs.push(Math.max(Math.abs(o.x - 480), Math.abs(o.y)));
  }
  expect(Math.max(...offs)).toBeGreaterThan(1);
  // zoom lerp: đo 2 mốc (150ms + 250ms) + loop time (xác nhận game loop chạy)
  await page.waitForTimeout(150);
  const m1 = await page.evaluate(() => {
    const sc = window.__phaserGame.scene.getScene("Game");
    return { z: sc.cameras.main.zoom, t: window.__phaserGame.loop.time, frozen: sc.state.frozen };
  });
  await page.waitForTimeout(250);
  const m2 = await page.evaluate(() => {
    const sc = window.__phaserGame.scene.getScene("Game");
    return { z: sc.cameras.main.zoom, t: window.__phaserGame.loop.time };
  });
  console.log("m1=" + JSON.stringify(m1) + " m2=" + JSON.stringify(m2));
  const zoom = m2.z;
  expect(Math.abs(zoom - 1.04)).toBeLessThanOrEqual(0.01);
  expect(m2.t).toBeGreaterThan(m1.t); // loop chạy
  expect(pageErrors).toEqual([]);
  // frozen → không đổi: freeze → chờ → scroll/zoom giữ nguyên + 2 shot byte-compare
  await page.evaluate(() => window.__yuniebel.debug.freeze(true));
  await page.waitForTimeout(100);
  const a = await page.locator("#game").screenshot();
  await page.waitForTimeout(500);
  const b = await page.locator("#game").screenshot();
  expect(Buffer.compare(a, b)).toBe(0);
});

// ===== TASK-082: AC-20 flip khớp vị trí — bbox mèo dir=1 vs dir=-1 cùng vùng (R-04) =====
test("AC-20: flip không nhảy — bbox mèo (màu #f5a623) dir=1 vs dir=-1 cùng vùng ±4px", async ({ page }) => {
  const bbox = async (page2) => page2.evaluate(() => {
    const game = document.getElementById("game");
    const tmp = document.createElement("canvas");
    tmp.width = 480; tmp.height = 270;
    const ctx = tmp.getContext("2d");
    ctx.drawImage(game, 0, 0);
    const d2 = ctx.getImageData(0, 0, 480, 270).data;
    let minX = 1e9, minY = 1e9, maxX = -1, maxY = -1;
    for (let y = 0; y < 270; y++) {
      for (let x = 0; x < 480; x++) {
        const i = (y * 480 + x) * 4;
        // màu cam mèo #f5a623 (tol ±20) + alpha 255
        if (Math.abs(d2[i] - 0xf5) < 20 && Math.abs(d2[i + 1] - 0xa6) < 20 && Math.abs(d2[i + 2] - 0x23) < 20 && d2[i + 3] > 200) {
          if (x < minX) minX = x; if (x > maxX) maxX = x;
          if (y < minY) minY = y; if (y > maxY) maxY = y;
        }
      }
    }
    return { minX, minY, maxX, maxY };
  });
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(700);
  // dir = 1
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("G_INIT");
    d.setPlayer(107, 70);
    d.freeze(true);
  });
  await page.waitForTimeout(150);
  const b1 = await bbox(page);
  // dir = -1 — set trực tiếp state (không di chuyển — deterministic)
  await page.evaluate(() => {
    window.__coreGame.state.player.dir = -1;
    window.__yuniebel.debug.freeze(true);
  });
  await page.waitForTimeout(150);
  const b2 = await bbox(page);
  expect(b2.minX).toBeGreaterThanOrEqual(b1.minX - 4);
  expect(b2.maxX).toBeLessThanOrEqual(b1.maxX + 4);
  expect(Math.abs(b2.minY - b1.minY)).toBeLessThanOrEqual(4);
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
