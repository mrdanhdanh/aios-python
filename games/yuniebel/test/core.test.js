/* core.test.js — Node test cho core.js (TASK-077)
 * Chạy: node test/core.test.js — exit code 0 = PASS
 */
"use strict";
const core = require("../src/core.js");

let passed = 0, failed = 0;
function assert(cond, name) {
  if (cond) { passed++; }
  else { failed++; console.error("  ✗ FAIL: " + name); }
}
function close(a, b, eps) { return Math.abs(a - b) < (eps || 0.001); }
function step(state, dt, input) { core.updateGame(state, dt, input || {}); }

// Di chuyển mèo tới gần target (đường ngắn; dừng khi có transition — tránh đi lung tung từ spawn mới)
function walkTo(state, tx, ty, dt) {
  const maxT = 30; let t = 0;
  const scene0 = state.scene, phase0 = state.phase;
  while (t < maxT) {
    if (state.scene !== scene0 || state.phase !== phase0) break; // dừng khi chuyển phase/scene
    const dx = tx - state.player.x, dy = ty - state.player.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < 4) break;
    const input = {};
    if (Math.abs(dx) > 4) { input.right = dx > 0; input.left = dx < 0; }
    if (Math.abs(dy) > 4) { input.down = dy > 0; input.up = dy < 0; }
    step(state, dt, input);
    t += dt;
  }
}
// Đặt mèo cạnh cửa GARDEN rồi bước vào → G_BUTTERFLY
function enterDoorZone(s) {
  s.player = { x: 818, y: 180, dir: 1, moving: false };
  for (let i = 0; i < 10 && s.phase === "G_INIT"; i++) step(s, 0.016, { right: true });
  return s.phase === "G_BUTTERFLY";
}
// Chạy hết chuỗi GARDEN tới LIVING
function passGarden(s) {
  enterDoorZone(s);                       // G_BUTTERFLY
  for (let i = 0; i < 110 && s.phase === "G_BUTTERFLY"; i++) step(s, 0.016, {}); // → G_CHASE
  if (s.butterfly) s.butterfly = { x: s.player.x + 10, y: s.player.y, alive: true }; // chạm bướm
  step(s, 0.016, {});                     // → G_DARK
  for (let i = 0; i < 420; i++) step(s, 0.016, {}); // tối 5s → G_DOOR → (mèo trong zone) LIVING
  return s.scene === "LIVING" && s.phase === "L_SEARCH";
}
// GARDEN + LIVING → KITCHEN/K_INIT
function passToKitchen(s) {
  if (!passGarden(s)) return false;
  walkTo(s, 35, 108, 0.016);              // cửa bếp (18..52, 85..131)
  step(s, 0.016, {});
  return s.scene === "KITCHEN" && s.phase === "K_INIT";
}
// Tới phase K_CHOICE
function toChoice(s) {
  if (!passToKitchen(s)) return false;
  walkTo(s, 375, 245, 0.016);             // vết máu (350..400, 235..255)
  step(s, 0.016, {});
  for (let i = 0; i < 120 && s.phase === "K_BLOOD"; i++) step(s, 0.016, {});
  for (let i = 0; i < 160 && s.phase === "K_VOICE"; i++) step(s, 0.016, {});
  return s.phase === "K_CHOICE";
}

console.log("=== TASK-077 core tests ===");

// ---- 1. resetGame / startGame ----
{
  const s = core.resetGame();
  assert(s.scene === "TITLE" && s.phase === "TITLE", "resetGame → TITLE");
  assert(s.scareCount === 0 && s.darkness === 0 && !s.butterfly, "resetGame fields clean");
  const s2 = core.startGame();
  assert(s2.scene === "GARDEN" && s2.phase === "G_INIT", "startGame → GARDEN/G_INIT");
  const s3 = core.resetGame();
  const s4 = core.resetGame();
  assert(JSON.stringify(s3) === JSON.stringify(s4), "resetGame 2 lần liên tục không lỗi, giống nhau");
}

// ---- 2. Di chuyển 4 hướng + biên map + collision ----
{
  const s = core.startGame();
  const y0 = s.player.y;
  step(s, 0.016, { right: true });
  assert(s.player.x > 420, "move right");
  step(s, 0.016, { left: true });
  assert(s.player.x < 420 + 2, "move left quay lại");
  step(s, 0.016, { down: true });
  assert(s.player.y > y0, "move down");
  const s2 = core.startGame();
  for (let i = 0; i < 300; i++) step(s2, 0.016, { left: true });
  assert(s2.player.x >= 0, "clamp biên trái (không âm)");
  const s3 = core.startGame();
  s3.player = { x: 330, y: 100, dir: 1, moving: false };
  for (let i = 0; i < 60; i++) step(s3, 0.016, { right: true });
  assert(s3.player.x < 350, "vật cản chặn (không xuyên bụi cây)");
}

// ---- 3. Chuỗi GARDEN: cửa khóa → bướm → tối → LIVING ----
{
  const s = core.startGame();
  assert(enterDoorZone(s), "chạm cửa ở G_INIT → G_BUTTERFLY (cửa khóa, mèo không vào được)");
  assert(s.butterfly && s.butterfly.alive, "bướm spawn");
  for (let i = 0; i < 110 && s.phase === "G_BUTTERFLY"; i++) step(s, 0.016, {});
  assert(s.phase === "G_CHASE", "G_BUTTERFLY → G_CHASE sau 1.5s");
  s.butterfly = { x: s.player.x + 10, y: s.player.y, alive: true };
  step(s, 0.016, {});
  assert(s.phase === "G_DARK" && !s.butterfly, "chạm bướm → G_DARK, bướm despawn");
  assert(close(s.darkness, 0, 0.02), "darkness bắt đầu ~0");
  s.player.x = 300; // mèo rời khỏi cửa (kiểm tra phase G_DOOR rõ ràng)
  for (let i = 0; i < 400; i++) step(s, 0.016, {});
  assert(s.darkness >= 1, "darkness đạt 1 sau 5s");
  assert(s.phase === "G_DOOR", "darkness=1 → G_DOOR (cửa mở)");
  walkTo(s, 845, 180, 0.016); // mèo quay lại cửa
  step(s, 0.016, {});
  assert(s.scene === "LIVING" && s.phase === "L_SEARCH", "vào cửa → LIVING/L_SEARCH");
}

// ---- 4. LIVING → KITCHEN ----
{
  const s = core.startGame();
  assert(passGarden(s), "passGarden → LIVING");
  walkTo(s, 35, 108, 0.016);
  step(s, 0.016, {});
  assert(s.scene === "KITCHEN" && s.phase === "K_INIT", "vào bếp → KITCHEN/K_INIT");
}

// ---- 5. KITCHEN: máu → lời gọi → chọn [1] → HAUNTED ----
{
  const s = core.startGame();
  assert(passToKitchen(s), "passToKitchen → KITCHEN/K_INIT");
  walkTo(s, 375, 245, 0.016);
  step(s, 0.016, {});
  assert(s.phase === "K_BLOOD", "chạm máu → K_BLOOD");
  for (let i = 0; i < 120 && s.phase === "K_BLOOD"; i++) step(s, 0.016, {});
  assert(s.phase === "K_VOICE", "K_BLOOD → K_VOICE sau 1.5s");
  for (let i = 0; i < 160 && s.phase === "K_VOICE"; i++) step(s, 0.016, {});
  assert(s.phase === "K_CHOICE", "K_VOICE → K_CHOICE sau 2s");
  // vùng tối = tường vô hình trước K_CHOICE
  const sBlock = core.startGame();
  assert(passToKitchen(sBlock), "sBlock tới KITCHEN");
  sBlock.player = { x: 100, y: 30, dir: -1, moving: false };
  step(sBlock, 0.016, { left: true });
  assert(sBlock.player.x >= 100 - 3, "vùng tối = tường vô hình trước K_CHOICE");
  // chọn [1] → chạy về phòng khách
  step(s, 0.016, { choice1: 1 });
  assert(s.phase === "K_RUN", "chọn 1 → K_RUN");
  for (let i = 0; i < 200; i++) step(s, 0.016, {});
  assert(s.scene === "HAUNTED" && s.phase === "H_SEARCH", "K_RUN → HAUNTED");
}

// ---- 6. KITCHEN: chọn [2] → GAMEOVER; đi vào vùng tối = GAMEOVER ----
{
  const s = core.startGame();
  assert(toChoice(s), "tới K_CHOICE (nhánh 2)");
  step(s, 0.016, { choice2: 2 });
  assert(s.phase === "K_OBEY", "chọn 2 → K_OBEY");
  for (let i = 0; i < 250; i++) step(s, 0.016, {});
  assert(s.scene === "GAMEOVER", "K_OBEY → GAMEOVER");

  const s2 = core.startGame();
  assert(toChoice(s2), "tới K_CHOICE (nhánh 3)");
  walkTo(s2, 65, 60, 0.016); // đi vào vùng tối (20..112, 20..120)
  step(s2, 0.016, {});
  assert(s2.phase === "K_OBEY", "đi vào vùng tối khi K_CHOICE → K_OBEY");
}

// ---- 7. HAUNTED: cửa trước knockback (lặp lại được), cửa hành lang → HALLWAY ----
{
  const s = core.startGame();
  core.setPhase(s, "H_SEARCH");
  s.scene = "HAUNTED";
  // Lần 1: mèo tiến sát cửa trước → knockback lùi, không chuyển cảnh
  s.player = { x: 416, y: 150, dir: 1, moving: false };
  step(s, 0.016, { right: true });
  assert(s.scene === "HAUNTED", "cửa trước không chuyển cảnh");
  assert(s.player.x < 400, "cửa trước → knockback lùi");
  assert(s.knockbackCd > 0, "knockback cooldown set");
  // spam trong cooldown: không bị đẩy lùi liên tục (không jitter)
  const xBefore = s.player.x;
  for (let i = 0; i < 40; i++) step(s, 0.016, { right: true });
  assert(s.player.x >= xBefore, "cooldown: không đẩy lùi tiếp");
  // Lần 2 sau cooldown: quay lại cửa → bị đẩy lần nữa
  s.knockbackCd = 0;
  s.player = { x: 416, y: 150, dir: 1, moving: false };
  step(s, 0.016, { right: true });
  assert(s.player.x < 400, "quay lại cửa → knockback lần 2");
  // cửa hành lang (205..245, 16..50)
  s.player = { x: 210, y: 30, dir: 1, moving: false };
  step(s, 0.016, {});
  assert(s.scene === "HALLWAY" && s.phase === "W_WALK", "cửa hành lang → HALLWAY/W_WALK");
}

// ---- 8. HALLWAY: 5 scare fire-once + mở cửa + one-way ----
{
  const s = core.startGame();
  core.setPhase(s, "W_WALK");
  s.scene = "HALLWAY";
  s.player = { x: 100, y: 135, dir: 1, moving: false };
  walkTo(s, 180, 135, 0.016);
  assert(s.scareCount === 1, "scare1 fire");
  assert(s.scareFlash, "scare flash set");
  walkTo(s, 150, 135, 0.016);
  walkTo(s, 180, 135, 0.016);
  assert(s.scareCount === 1, "scare1 không fire lặp (fire-once)");
  walkTo(s, 340, 135, 0.016);
  assert(s.scareCount === 2, "scare2 fire");
  walkTo(s, 500, 135, 0.016);
  assert(s.scareCount === 3, "scare3 fire");
  walkTo(s, 660, 135, 0.016);
  assert(s.scareCount === 4, "scare4 fire");
  walkTo(s, 820, 135, 0.016);
  assert(s.scareCount === 5 && s.phase === "W_DONE", "scare5 → W_DONE (mở cửa)");
  walkTo(s, 920, 135, 0.016);
  step(s, 0.016, {});
  assert(s.scene === "DINING" && s.phase === "D_APPROACH", "cửa phòng ăn → DINING");
  // one-way: wall chặn cửa vào (0..28, 100..170)
  s.player = { x: 30, y: 135, dir: -1, moving: false };
  step(s, 0.016, { left: true });
  assert(s.player.x >= 24, "cửa vào đóng (one-way)");
}

// ---- 9. DINING cutscene ----
{
  const s = core.startGame();
  core.setPhase(s, "D_APPROACH");
  s.scene = "DINING";
  s.player = { x: 150, y: 220, dir: 1, moving: false };
  for (let i = 0; i < 10 && s.phase === "D_APPROACH"; i++) step(s, 0.016, { right: true });
  assert(s.phase === "D_JUMP", "approach → D_JUMP (cutscene, lock input)");
  const x0 = s.player.x;
  step(s, 0.016, { right: true });
  assert(Math.abs(s.player.x - x0) < 0.1, "input lock trong D_JUMP");
  for (let i = 0; i < 100; i++) step(s, 0.016, {});
  assert(s.phase === "D_HUG" && s.chimeFlag, "D_JUMP → D_HUG + chime flag");
  for (let i = 0; i < 140; i++) step(s, 0.016, {});
  assert(s.phase === "D_CAKE", "D_HUG → D_CAKE");
  for (let i = 0; i < 220; i++) step(s, 0.016, {});
  assert(s.scene === "END", "D_CAKE → END");
}

// ---- 10. Không dt → không transition ----
{
  const s = core.startGame();
  step(s, 0, {});
  assert(s.phase === "G_INIT", "dt=0 → không transition");
}

// ---- 11. Light radius ----
{
  const s = core.startGame();
  core.setPhase(s, "H_SEARCH");
  s.scene = "HAUNTED";
  assert(core.hasDark(s), "HAUNTED → hasDark");
  s.player = { x: 240, y: 135, dir: 1, moving: false };
  assert(core.inLight(s, 240, 135), "tại mèo → inLight");
  assert(!core.inLight(s, 240 + core.LIGHT_RADIUS + 10, 135), "ngoài bán kính → không inLight");
  const s2 = core.startGame();
  assert(!core.hasDark(s2), "GARDEN G_INIT → không tối");
}

// ---- 12. reset qua input.start (Game Over → chơi lại) ----
{
  const s = core.startGame();
  s.scene = "GAMEOVER"; s.phase = "GAMEOVER";
  step(s, 0.016, { start: true });
  assert(s.scene === "GARDEN" && s.phase === "G_INIT", "input.start từ GAMEOVER → chơi lại");
}

console.log("PASS: " + passed + " / " + (passed + failed));
if (failed > 0) {
  console.error("FAILED: " + failed);
  process.exit(1);
}
