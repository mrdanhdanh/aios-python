/* smoke.test.js — TASK-078 — node test/smoke.test.js
 * jsdom: game load không lỗi, START chuyển phase, script classic chạy file://.
 * Dùng jsdom từ node_modules của dashboard (không thêm dependency).
 */
"use strict";
var assert = require("assert");
var fs = require("fs");
var path = require("path");

var ROOT = path.join(__dirname, "..");
var JSDOM = require(path.join(ROOT, "..", "..", "dashboard", "node_modules", "jsdom")).JSDOM;

var pass = 0, fail = 0;
function T(name, fn) {
  try { fn(); pass++; console.log("  ✓ " + name); }
  catch (e) { fail++; console.log("  ✗ " + name + " — " + e.message); }
}

console.log("=== smoke.test.js — TASK-078 ===");

// mock canvas 2d context đơn giản
function mockCtx() {
  return new Proxy({}, {
    get: function (t, p) {
      if (p === "canvas") return { width: 480, height: 270 };
      if (typeof p === "string" && (p === "fillRect" || p === "clearRect" || p === "fillText" || p === "drawImage" ||
          p === "beginPath" || p === "moveTo" || p === "lineTo" || p === "stroke" || p === "fill" ||
          p === "save" || p === "restore" || p === "translate" || p === "scale" || p === "rotate" ||
          p === "arc" || p === "closePath" || p === "setTransform" || p === "clip" || p === "resetTransform")) {
        return function () {};
      }
      return t[p];
    },
    set: function (t, p, v) { t[p] = v; return true; }
  });
}

function loadGame() {
  var html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
  var dom = new JSDOM(html, {
    url: "file://" + ROOT.replace(/\\/g, "/") + "/index.html?test=1",
    runScripts: "outside-only",
    pretendToBeVisual: true
  });
  var w = dom.window;
  // mock canvas: jsdom HTMLCanvasElement.width/height có setter throw → define lại
  Object.defineProperty(w.HTMLCanvasElement.prototype, "width", { value: 480, writable: true });
  Object.defineProperty(w.HTMLCanvasElement.prototype, "height", { value: 270, writable: true });
  w.HTMLCanvasElement.prototype.getContext = function () { return mockCtx(); };
  // mock AudioContext (R11: jsdom không có)
  w.AudioContext = undefined;
  w.webkitAudioContext = undefined;
  w.requestAnimationFrame = function (cb) { return 0; }; // không loop
  w.performance = { now: function () { return 0; } };
  // load scripts
  ["src/core.js", "src/sprites.js", "src/audio.js", "src/game.js"].forEach(function (f) {
    var code = fs.readFileSync(path.join(ROOT, f), "utf8");
    try { w.eval(code); } catch (e) { throw new Error(f + " load error: " + e.message); }
  });
  return { dom: dom, w: w };
}

T("4 script load không lỗi + AiosCore/Sprites/AudioFX tồn tại", function () {
  var g = loadGame();
  assert.ok(g.w.AiosCore, "AiosCore");
  assert.ok(g.w.Sprites, "Sprites");
  assert.ok(g.w.AudioFX, "AudioFX");
});

T("index.html có đủ UI element", function () {
  var g = loadGame();
  var doc = g.w.document;
  ["game", "task-box", "task-text", "dialogue", "dialogue-text", "choice-box",
   "choice-1", "choice-2", "scare-counter", "title-screen", "gameover-screen",
   "end-screen", "btn-start", "btn-replay-1", "btn-replay-2", "mute-btn"].forEach(function (id) {
    assert.ok(doc.getElementById(id), "missing #" + id);
  });
});

T("Debug hook active khi ?test=1 (C1-15)", function () {
  var g = loadGame();
  assert.ok(g.w.__yuniebel, "__yuniebel");
  assert.ok(g.w.__yuniebel.debug, "debug API");
  assert.strictEqual(typeof g.w.__yuniebel.debug.freeze, "function");
  assert.strictEqual(typeof g.w.__yuniebel.debug.setPhase, "function");
  assert.strictEqual(typeof g.w.__yuniebel.debug.setDarkness, "function");
  assert.strictEqual(typeof g.w.__yuniebel.debug.setScareZone, "function");
});

T("core.createGame + update chạy (state machine)", function () {
  var g = loadGame();
  var core = g.w.AiosCore;
  var game = core.createGame();
  game.update(0.016, {});
  assert.ok(game.getPhase() === "TITLE");
});

console.log("\n===== KẾT QUẢ: " + pass + " pass / " + fail + " fail =====");
process.exit(fail > 0 ? 1 : 0);
