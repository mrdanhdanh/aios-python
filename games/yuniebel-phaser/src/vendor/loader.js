/* loader.js — adapter import UMD vendor (TASK-081, file RIÊNG — vendor byte-identical, AC-16)
 * Vấn đề: Vite CJS-interop transform file chứa `module.exports` thành ESM wrapper →
 * nhánh browser (root.AiosCore = ...) KHÔNG chạy khi import trực tiếp.
 * Giải pháp: nhúng raw (?raw) + indirect eval (global scope) → UMD gán window như browser.
 * KHÔNG sửa 3 file vendor (diff --no-index phải sạch).
 */
import coreRaw from "./core.js?raw";
import spritesRaw from "./sprites.js?raw";
import audioRaw from "./audio.js?raw";

function execGlobal(src) {
  // indirect eval → chạy trong global scope (strict ESM không chặn indirect eval)
  (0, eval)(src);
}

if (typeof window !== "undefined") {
  if (!window.AiosCore) execGlobal(coreRaw);
  if (!window.Sprites) execGlobal(spritesRaw);
  if (!window.AudioFX) execGlobal(audioRaw);
}

export {};
