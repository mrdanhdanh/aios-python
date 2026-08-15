/* smoke.test.js — Smoke test browser environment (jsdom)
 * Chạy: node test/smoke.test.js — exit 0 = PASS
 * Yêu cầu: node_modules của dashboard (jsdom) — dùng đường dẫn tương đối.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");

let jsdom;
try {
  jsdom = require(path.join(__dirname, "../../../dashboard/node_modules/jsdom"));
} catch (e) {
  try { jsdom = require("jsdom"); } catch (e2) {
    console.error("SKIP: cần jsdom (dashboard/node_modules hoặc cài global)");
    process.exit(0);
  }
}
const { JSDOM } = jsdom;

let passed = 0, failed = 0;
function assert(cond, name) {
  if (cond) { passed++; }
  else { failed++; console.error("  ✗ FAIL: " + name); }
}

// Mock canvas 2D context (jsdom không hỗ trợ)
function mockCtx() {
  const noop = function () {};
  return new Proxy({}, {
    get: (t, p) => {
      if (p === "canvas") return { width: 480, height: 270 };
      if (p === "createLinearGradient" || p === "createRadialGradient") return () => ({ addColorStop: noop });
      if (typeof p === "string") return noop;
      return undefined;
    },
    set: () => true
  });
}

const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "outside-only", pretendToBeVisual: true, url: "file:///games/yuniebel/index.html" });
const win = dom.window;
const doc = win.document;

win.HTMLCanvasElement.prototype.getContext = function () { return mockCtx(); };

// Driver rAF thủ công — override TRƯỚC khi eval game.js
let rafQueue = [];
win.requestAnimationFrame = (cb) => { rafQueue.push(cb); };
let t = 0;

// Inject scripts theo thứ tự
for (const src of ["src/core.js", "src/sprites.js", "src/audio.js", "src/game.js"]) {
  const code = fs.readFileSync(path.join(ROOT, src), "utf8");
  win.eval(code);
}

function tick() {
  const q = rafQueue.splice(0);
  q.forEach((cb) => { try { cb(t); } catch (e) { console.error("  ✗ rAF throw:", e.message); failed++; } });
  t += 16.7;
}
// frame 1 (set last) + vài frame
for (let i = 0; i < 5; i++) tick();

console.log("=== TASK-077 smoke tests ===");
const game = win.__yuniebel;

assert(game && game.getState, "game loaded (window.__yuniebel)");
assert(game.getState().scene === "TITLE", "khởi động ở TITLE");

// Click START
doc.getElementById("btn-start").click();
tick();
tick();
let st = game.getState();
assert(st.scene === "GARDEN" && st.phase === "G_INIT", "START → GARDEN/G_INIT");
assert(doc.getElementById("title-screen").classList.contains("hidden"), "title screen ẩn sau START");
assert(!doc.getElementById("task-box").classList.contains("hidden"), "task box hiện khi chơi");
assert(doc.getElementById("task-text").textContent.length > 0, "task text có nội dung");

// Bấm W → mèo di chuyển lên
const y0 = st.player.y;
win.dispatchEvent(new win.KeyboardEvent("keydown", { key: "w", bubbles: true }));
for (let i = 0; i < 10; i++) tick();
st = game.getState();
assert(st.player.y < y0 - 5, "bấm W → mèo đi lên");
win.dispatchEvent(new win.KeyboardEvent("keyup", { key: "w", bubbles: true }));

// Bấm X → về TITLE + reset
doc.getElementById("task-close").click();
st = game.getState();
assert(st.scene === "TITLE", "nút X → về TITLE");
assert(doc.getElementById("title-screen") && !doc.getElementById("title-screen").classList.contains("hidden"), "title screen hiện lại");

// START lại lần nữa — không crash
doc.getElementById("btn-start").click();
for (let i = 0; i < 60; i++) tick(); // 1 giây gameplay
st = game.getState();
assert(st.scene === "GARDEN", "chơi lại không crash (1s frame)");
assert(st.time > 0.5, "game time chạy");

// Toggle UI
doc.getElementById("ui-toggle").click();
assert(doc.getElementById("task-box").classList.contains("hidden"), "toggle UI → ẩn task box");
doc.getElementById("ui-toggle").click();
assert(!doc.getElementById("task-box").classList.contains("hidden"), "toggle UI → hiện lại");

// ---- Render mọi cảnh không crash (mutate state thật qua getState) ----
const real = game.getState();
const scenesToTest = [
  ["GARDEN", "G_INIT"],
  ["GARDEN", "G_DARK"],
  ["LIVING", "L_SEARCH"],
  ["KITCHEN", "K_INIT"],
  ["KITCHEN", "K_CHOICE"],
  ["KITCHEN", "K_OBEY"],
  ["HAUNTED", "H_SEARCH"],
  ["HALLWAY", "W_WALK"],
  ["HALLWAY", "W_DONE"],
  ["DINING", "D_APPROACH"],
  ["DINING", "D_HUG"],
  ["DINING", "D_CAKE"],
  ["GAMEOVER", "GAMEOVER"],
  ["END", "END"],
  ["TITLE", "TITLE"]
];
for (const [sc, ph] of scenesToTest) {
  real.scene = sc; real.phase = ph;
  real.player = { x: 240, y: 135, dir: 1, moving: false };
  real.butterfly = null;
  real.darkness = 0;
  real.scareCount = 0;
  real.scareFlash = null;
  real.message = null;
  real.chimeFlag = false;
  if (sc === "GARDEN") real.butterfly = { x: 300, y: 100, alive: true };
  if (ph === "G_DARK" || ph === "K_OBEY") real.darkness = 0.6;
  if (sc === "HALLWAY") real.scareCount = 2;
  if (ph === "D_HUG" || ph === "D_CAKE") real.chimeFlag = true;
  if (ph === "D_HUG") real.message = { text: "Happy Birthday Yuniebel!", until: 999 };
  try {
    for (let i = 0; i < 10; i++) tick();
    assert(true, "render cảnh " + sc + "/" + ph + " không crash");
  } catch (e) {
    assert(false, "render cảnh " + sc + "/" + ph + " crash: " + e.message);
  }
}

console.log("PASS: " + passed + " / " + (passed + failed));
if (failed > 0) {
  console.error("FAILED: " + failed);
  process.exit(1);
}
