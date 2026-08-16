/* main.js — Yuniebel's Cat (TASK-081, bản Phaser 4) — bootstrap
 * Vendor UMD (window.AiosCore/Sprites/AudioFX) + input window listeners + resize CSS
 * + Phaser.Game (canvas#game 480×270, pixelArt) + debug hook ?test=1.
 * Port từ game.js vanilla — KHÔNG đổi hành vi.
 */
import Phaser from "phaser";
import "./vendor/loader.js"; // UMD adapter → window.AiosCore/Sprites/AudioFX (AC-16: vendor byte-identical)
import GameScene from "./scenes/GameScene.js";

const core = window.AiosCore;
const audio = window.AudioFX();
const game = core.createGame();
window.__coreGame = game;
window.__audioFX = audio;

// ===== INPUT (port nguyên văn game.js vanilla — P3-3: window listeners, e.repeat guard) =====
var keys = {}, dpad = { up: false, down: false, left: false, right: false };
var isTouch = ("ontouchstart" in window) || navigator.maxTouchPoints > 0;
var oneShot = { start: false, choice1: false, choice2: false };
window.__keys = keys;
window.__dpad = dpad;
window.__oneShot = oneShot;

function kN(e) { return e.key.toLowerCase(); }
window.addEventListener("keydown", function (e) {
  var k = kN(e);
  if (["w", "a", "s", "d", "arrowup", "arrowdown", "arrowleft", "arrowright", " "].indexOf(k) !== -1) e.preventDefault();
  if (e.repeat) return;
  audio.init(); // C2-15: gesture đầu resume
  keys[k] = true;
  if (k === "1" && game.state.phase === "K_CHOICE") oneShot.choice1 = true;
  if (k === "2" && game.state.phase === "K_CHOICE") oneShot.choice2 = true;
  if ((k === "enter" || k === " ") && (game.state.scene === "TITLE" || game.state.scene === "GAMEOVER" || game.state.scene === "END")) oneShot.start = true;
});
window.addEventListener("keyup", function (e) { keys[kN(e)] = false; });
window.addEventListener("blur", function () { for (var k in keys) keys[k] = false; });
document.addEventListener("visibilitychange", function () {
  if (document.hidden) { for (var k in keys) keys[k] = false; } else audio.init();
});

function bPad(id, dir) {
  var el = document.getElementById(id); if (!el) return;
  el.addEventListener("touchstart", function (e) { e.preventDefault(); dpad[dir] = true; audio.init(); });
  el.addEventListener("touchend", function (e) { e.preventDefault(); dpad[dir] = false; });
  el.addEventListener("touchcancel", function () { dpad[dir] = false; });
}
bPad("pad-up", "up"); bPad("pad-down", "down"); bPad("pad-left", "left"); bPad("pad-right", "right");
if (isTouch) { document.getElementById("dpad").classList.remove("hidden"); document.getElementById("hint").classList.add("hidden"); }

// ===== RESIZE (P2-B4: KHÔNG Scale Manager — CSS letterbox như vanilla) =====
function resize() {
  var CW = 480, CH = 270;
  var w = window.innerWidth, h = window.innerHeight;
  var s = Math.min(w / CW, h / CH);
  var el = document.getElementById("game");
  el.style.width = Math.floor(CW * s) + "px";
  el.style.height = Math.floor(CH * s) + "px";
}
window.addEventListener("resize", resize);
resize();

// ===== Phaser boot (canvas#game có sẵn — P3-4; bắt buộc width/height 480×270 — review)
// Phaser 4: khi truyền `canvas` tùy chỉnh (custom environment) PHẢI khai báo renderType tường minh
// (AUTO bị từ chối: "Must set explicit renderType in custom environment") → dùng WEBGL, fallback CANVAS.
const renderType = (() => {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl") || c.getContext("experimental-webgl")) ? Phaser.WEBGL : Phaser.CANVAS;
  } catch (e) { return Phaser.CANVAS; }
})();
const phaserGame = new Phaser.Game({
  type: renderType,
  canvas: document.getElementById("game"),
  width: 480,
  height: 270,
  pixelArt: true,
  roundPixels: true,
  backgroundColor: "#000000",
  scene: [GameScene]
});
window.__phaserGame = phaserGame;

// ===== DEBUG HOOK (chỉ khi ?test=1 — C1-15; camX expose — P1-2/AC-7) =====
if (/[?&]test=1/.test(window.location.search)) {
  window.__yuniebel = {
    debug: game.debug,
    getState: function () { return game.state; },
    camX: function () {
      var sc = core.SCENES[game.state.scene];
      if (!sc) return 0;
      return Math.max(0, Math.min(game.state.player.x - 80 + 3, sc.w - 160));
    },
    core: core,
    audio: audio
  };
}
