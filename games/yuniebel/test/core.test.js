/* core.test.js — TASK-078 — node test/core.test.js
 * Test logic thuần: state machine, 13 câu thoại canonical, task §6.1, bướm, scare 5/5, choice.
 */
"use strict";
var assert = require("assert");
var core = require("../src/core.js");

var pass = 0, fail = 0;
function T(name, fn) {
  try { fn(); pass++; console.log("  ✓ " + name); }
  catch (e) { fail++; console.log("  ✗ " + name + " — " + e.message); }
}
function near(a, b, eps) { return Math.abs(a - b) < (eps || 1e-6); }

console.log("=== core.test.js — TASK-078 ===");

// ===== 1. Hội thoại canonical (AC-1): 13 câu khớp brief =====
console.log("\n[AC-1] 13 câu thoại canonical");
T("G_INIT có 2 câu đúng brief", function () {
  var d = core.DIALOGUES.G_INIT;
  assert.strictEqual(d.length, 2);
  assert.strictEqual(d[0].text, "Yuniebel! Vào nhà đi!");
  assert.strictEqual(d[0].thought, false);
  assert.strictEqual(d[0].speaker, "owner");
  assert.strictEqual(d[1].text, "Meow~ Nhưng ngoài này vui quá…");
  assert.strictEqual(d[1].thought, true);
  assert.strictEqual(d[1].speaker, "cat");
});
T("L_SEARCH đúng brief", function () {
  var d = core.DIALOGUES.L_SEARCH;
  assert.strictEqual(d[0].text, "Meow? Chủ nhân đâu rồi?");
});
T("K_INIT + K_BLOOD đúng brief", function () {
  assert.strictEqual(core.DIALOGUES.K_INIT[0].text, "Meow… có gì đó lạ…");
  var d = core.DIALOGUES.K_BLOOD;
  assert.strictEqual(d[0].text, "Meow?! Đây là gì vậy?");
  assert.strictEqual(d[1].text, "Đến đây đi… Meow…");
  assert.strictEqual(d[1].speaker, "dark");
});
T("H_INIT đúng brief", function () {
  var d = core.DIALOGUES.H_INIT;
  assert.strictEqual(d[0].text, "Meow… căn phòng này… khác rồi…");
  assert.strictEqual(d[1].text, "Không được rời đi…");
  assert.strictEqual(d[1].speaker, "ghost");
});
T("W_INIT đúng brief", function () {
  assert.strictEqual(core.DIALOGUES.W_INIT[0].text, "Meow… mình phải đi tiếp…");
});
T("D_END 3 câu đúng brief", function () {
  var d = core.DIALOGUES.D_END;
  assert.strictEqual(d[0].text, "Happy Birthday Yuniebel!");
  assert.strictEqual(d[0].speaker, "owner");
  assert.strictEqual(d[1].text, "Meow~");
  assert.strictEqual(d[1].speaker, "cat");
  assert.strictEqual(d[2].text, "Chúc Mừng Sinh Nhật!");
  assert.strictEqual(d[2].speaker, "owner");
});
T("Tổng 12 câu trong DIALOGUES + 'Meow!!' khi hù = 13 (C1-05)", function () {
  var total = 0;
  for (var k in core.DIALOGUES) total += core.DIALOGUES[k].length;
  assert.strictEqual(total, 12);
  // câu 13 "Meow!!" được đặc tả trong W_WALK khi scare — kiểm tra qua simulate
  var s = core.startGame();
  core.setPhase(s, "W_WALK");
  s.player.x = 160; s.player.y = 130; // scare zone 1
  core.updateGame(s, 0.016, {});
  assert.strictEqual(s.dialogue.text, "Meow!!");
});

// ===== 2. Task canonical (§6.1 — AC-2) =====
console.log("\n[AC-2] Task text canonical");
T("Bảng phase→task đúng §6.1", function () {
  var expect = {
    G_INIT: "Đuổi theo con bướm!", G_CHASE: "Đuổi theo con bướm!",
    G_DARK: "Hãy vào nhà!", G_DOOR: "Hãy vào nhà!",
    L_SEARCH: "Tìm chủ nhân ở nhà bếp.",
    K_INIT: "Kiểm tra vết máu!", K_BLOOD: "Kiểm tra vết máu!", K_CHOICE: "Kiểm tra vết máu!",
    H_INIT: "Tìm người chủ!",
    H_BLOCK: "Phải đi qua phòng khác!", H_EXIT: "Phải đi qua phòng khác!",
    W_INIT: "Đi qua hành lang.", W_WALK: "Đi qua hành lang.",
    W_DONE: "Đã đến phòng ăn.",
    D_END: "Hoàn thành nhiệm vụ: Tìm chủ nhân."
  };
  for (var p in expect) {
    assert.strictEqual(core.PHASES[p].task, expect[p], "phase " + p);
  }
});

// ===== 3. Chuỗi kịch bản (AC-10/AC-14) =====
console.log("\n[AC-10/14] Chuỗi kịch bản");
T("Bắt đầu: START → G_INIT + dialogue chủ gọi", function () {
  var s = core.startGame();
  assert.strictEqual(s.phase, "G_INIT");
  assert.strictEqual(s.scene, "GARDEN");
  assert.strictEqual(s.player.x, core.SCENES.GARDEN.spawn.x);
});
T("R-01: dialogue G_INIT hiển thị NGAY sau startGame (câu 1 'Yuniebel! Vào nhà đi!')", function () {
  var s = core.startGame();
  assert.ok(s.dialogue, "dialogue phải active");
  assert.strictEqual(s.dialogue.text, "Yuniebel! Vào nhà đi!");
  assert.strictEqual(s.dialogue.speaker, "owner");
  // sau 1 frame vẫn hiển thị (chưa advance)
  core.updateGame(s, 0.016, {});
  assert.strictEqual(s.dialogue.text, "Yuniebel! Vào nhà đi!");
  // hết dur → câu 2
  for (var i = 0; i < 200; i++) core.updateGame(s, 0.016, {});
  assert.ok(s.dialogue, "câu 2 hiển thị");
  assert.strictEqual(s.dialogue.text, "Meow~ Nhưng ngoài này vui quá…");
  assert.strictEqual(s.dialogue.thought, true);
});
T("R-02: startGame set soundFlags.start (resetStats màn chơi mới)", function () {
  var s = core.startGame();
  assert.strictEqual(s.soundFlags.start, true);
});
T("Mèo tiến gần cửa (x>780) → bướm xuất hiện + ting", function () {
  var s = core.startGame();
  s.player.x = 790; s.player.y = 150;
  core.updateGame(s, 0.016, {});
  assert.ok(s.butterfly, "bướm phải xuất hiện");
  assert.strictEqual(s.soundFlags.ting, true);
});
T("Bắt bướm → G_DARK + darkness ramp 5s (R7)", function () {
  var s = core.startGame();
  s.butterfly = { x: s.player.x + 5, y: s.player.y + 5, wp: 0, stayT: 0, flap: 0 };
  core.updateGame(s, 0.016, {});
  assert.strictEqual(s.phase, "G_DARK");
  assert.ok(s.timers.dark > 0);
  assert.strictEqual(s.darkness, 0);
  // sau 5s → G_DOOR
  for (var i = 0; i < 400; i++) core.updateGame(s, 0.016, {});
  assert.strictEqual(s.phase, "G_DOOR");
});
T("Vào cửa (G_DOOR) → L_SEARCH + dialogue 'Meow? Chủ nhân đâu rồi?'", function () {
  var s = core.startGame();
  core.setPhase(s, "G_DOOR");
  s.player.x = 860; s.player.y = 160;
  core.updateGame(s, 0.016, {});
  assert.strictEqual(s.phase, "L_SEARCH");
  assert.strictEqual(s.dialogue.text, "Meow? Chủ nhân đâu rồi?");
});
T("Phòng khách → cửa bếp → K_INIT", function () {
  var s = core.startGame();
  core.setPhase(s, "L_SEARCH");
  s.player.x = 20; s.player.y = 100;
  core.updateGame(s, 0.016, {});
  assert.strictEqual(s.phase, "K_INIT");
  assert.strictEqual(s.dialogue.text, "Meow… có gì đó lạ…");
});
T("Chạm vết máu → K_BLOOD → hết dialogue → K_CHOICE", function () {
  var s = core.startGame();
  core.setPhase(s, "K_INIT");
  s.player.x = 190; s.player.y = 240;
  core.updateGame(s, 0.016, {});
  assert.strictEqual(s.phase, "K_BLOOD");
  assert.strictEqual(s.dialogue.text, "Meow?! Đây là gì vậy?");
  // advance dialogue rồi chạm vùng tối
  for (var i = 0; i < 10; i++) core.updateGame(s, 0.016, {});
  s.dialogue = null; s.dialogueQueue = [];
  s.player.x = 40; s.player.y = 40;
  core.updateGame(s, 0.016, {});
  assert.strictEqual(s.phase, "K_CHOICE");
});
T("Chọn 2 → GAME_OVER + swoosh + painMeow (AC-10)", function () {
  var s = core.startGame();
  core.setPhase(s, "K_CHOICE");
  core.updateGame(s, 0.016, { choice2: true });
  assert.strictEqual(s.phase, "GAME_OVER");
  assert.strictEqual(s.choice, 2);
  assert.strictEqual(s.soundFlags.swoosh, true);
  assert.strictEqual(s.soundFlags.painMeow, true);
});
T("Chọn 1 → H_INIT + rush (AC-10)", function () {
  var s = core.startGame();
  core.setPhase(s, "K_CHOICE");
  core.updateGame(s, 0.016, { choice1: true });
  assert.strictEqual(s.phase, "H_INIT");
  assert.strictEqual(s.choice, 1);
  assert.strictEqual(s.soundFlags.rush, true);
});
T("H_INIT hết dialogue → H_BLOCK + ma đẩy lùi + đổi task (C1-14)", function () {
  var s = core.startGame();
  core.setPhase(s, "H_INIT");
  s.dialogue = null;
  s.dialogueQueue = []; // R-01: queue cũ không được advance vào H_INIT
  core.updateGame(s, 0.016, {});
  assert.strictEqual(s.phase, "H_BLOCK");
  // cố ra cửa chính → knockback
  s.player.x = 430; s.player.y = 150;
  var x0 = s.player.x;
  core.updateGame(s, 0.016, {});
  assert.ok(s.player.x < x0, "mèo bị đẩy lùi");
  assert.strictEqual(s.ghostBlocked, true);
  assert.strictEqual(core.PHASES[s.phase].task, "Phải đi qua phòng khác!");
});
T("Cửa phụ trái → W_INIT (không deadlock — C2-03)", function () {
  var s = core.startGame();
  core.setPhase(s, "H_EXIT");
  s.player.x = 10; s.player.y = 100;
  core.updateGame(s, 0.016, {});
  assert.strictEqual(s.phase, "W_INIT");
  assert.strictEqual(s.scene, "HALLWAY");
});
T("5 scare zone → W_DONE + 'Meow!!' mỗi lần (AC-8)", function () {
  var s = core.startGame();
  core.setPhase(s, "W_WALK");
  var zones = core.SCENES.HALLWAY.scareZones;
  for (var i = 0; i < zones.length; i++) {
    s.player.x = zones[i].x + 10; s.player.y = zones[i].y + 10;
    core.updateGame(s, 0.016, {});
    if (i < 4) {
      assert.strictEqual(s.phase, "W_WALK", "scare " + (i + 1) + " chưa kết thúc");
      assert.strictEqual(s.scareActive, i + 1, "scareActive = " + (i + 1));
      assert.strictEqual(s.dialogue.text, "Meow!!");
      // R-04: scare hết hạn sau ~1.5s
      for (var j = 0; j < 120; j++) core.updateGame(s, 0.016, {});
      assert.strictEqual(s.scareActive, 0, "scare phải hết hạn sau 1.5s");
    }
  }
  assert.strictEqual(s.scareCount, 5);
  assert.strictEqual(s.phase, "W_DONE");
});
T("W_DONE → cửa → D_END + 3 câu thoại sinh nhật (AC-9)", function () {
  var s = core.startGame();
  core.setPhase(s, "W_DONE");
  s.player.x = 910; s.player.y = 130;
  core.updateGame(s, 0.016, {});
  assert.strictEqual(s.phase, "D_END");
  assert.strictEqual(s.dialogue.text, "Happy Birthday Yuniebel!");
});
T("D_END hết thoại + 3s → END + bell (R6)", function () {
  var s = core.startGame();
  core.setPhase(s, "D_END");
  s.dialogue = null; s.dialogueQueue = [];
  for (var i = 0; i < 300; i++) core.updateGame(s, 0.016, {});
  assert.strictEqual(s.phase, "END");
  assert.strictEqual(s.soundFlags.bell, true);
});
T("GAME OVER → START lại → G_INIT (reset)", function () {
  var s = core.startGame();
  core.setPhase(s, "GAME_OVER");
  core.updateGame(s, 0.016, { start: true });
  assert.strictEqual(s.phase, "G_INIT");
  assert.ok(s.dialogue, "dialogue mới hiển thị sau reset (R-01)");
});

// ===== 4. Collision (AC-14) =====
console.log("\n[Collision]");
T("Không xuyên tường nhà (GARDEN)", function () {
  var s = core.startGame();
  s.player.x = 790; s.player.y = 50;
  var x0 = s.player.x;
  core.updateGame(s, 0.016, { right: true });
  assert.ok(s.player.x <= x0 + 2);
});
T("Không ra ngoài biên map", function () {
  var s = core.startGame();
  s.player.x = 0; s.player.y = 0;
  core.updateGame(s, 0.1, { left: true, up: true });
  assert.ok(s.player.x >= 0 && s.player.y >= 0);
});

// ===== 5. Debug API =====
console.log("\n[Debug API]");
T("freeze(true) đóng băng state.time (R1)", function () {
  var s = core.startGame();
  var t0 = s.time;
  s.frozen = true;
  core.updateGame(s, 0.5, {});
  assert.strictEqual(s.time, t0);
});

console.log("\n===== KẾT QUẢ: " + pass + " pass / " + fail + " fail =====");
process.exit(fail > 0 ? 1 : 0);
