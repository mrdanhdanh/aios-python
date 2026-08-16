/* core.test.js — TASK-081 (bản Phaser) — vitest (environment jsdom)
 * Migrate 27 assertion từ games/yuniebel/test/core.test.js (TASK-078).
 * Vendor byte-identical (AC-16); import side-effect → window.AiosCore (P3-B2).
 * Bỏ process.exit (R3) — dùng expect từ vitest.
 */
import { expect, test } from "vitest";
import "../src/vendor/loader.js"; // UMD adapter → window.AiosCore (P3-B2 — vendor byte-identical)

const core = window.AiosCore;

function T(name, fn) {
  test(name, () => {
    fn();
  });
}

// ===== 1. Hội thoại canonical (AC-1): 13 câu khớp brief =====
T("G_INIT có 2 câu đúng brief", function () {
  var d = core.DIALOGUES.G_INIT;
  expect(d.length).toBe(2);
  expect(d[0].text).toBe("Yuniebel! Vào nhà đi!");
  expect(d[0].thought).toBe(false);
  expect(d[0].speaker).toBe("owner");
  expect(d[1].text).toBe("Meow~ Nhưng ngoài này vui quá…");
  expect(d[1].thought).toBe(true);
  expect(d[1].speaker).toBe("cat");
});
T("L_SEARCH đúng brief", function () {
  var d = core.DIALOGUES.L_SEARCH;
  expect(d[0].text).toBe("Meow? Chủ nhân đâu rồi?");
});
T("K_INIT + K_BLOOD đúng brief", function () {
  expect(core.DIALOGUES.K_INIT[0].text).toBe("Meow… có gì đó lạ…");
  var d = core.DIALOGUES.K_BLOOD;
  expect(d[0].text).toBe("Meow?! Đây là gì vậy?");
  expect(d[1].text).toBe("Đến đây đi… Meow…");
  expect(d[1].speaker).toBe("dark");
});
T("H_INIT đúng brief", function () {
  var d = core.DIALOGUES.H_INIT;
  expect(d[0].text).toBe("Meow… căn phòng này… khác rồi…");
  expect(d[1].text).toBe("Không được rời đi…");
  expect(d[1].speaker).toBe("ghost");
});
T("W_INIT đúng brief", function () {
  expect(core.DIALOGUES.W_INIT[0].text).toBe("Meow… mình phải đi tiếp…");
});
T("D_END 3 câu đúng brief", function () {
  var d = core.DIALOGUES.D_END;
  expect(d[0].text).toBe("Happy Birthday Yuniebel!");
  expect(d[0].speaker).toBe("owner");
  expect(d[1].text).toBe("Meow~");
  expect(d[1].speaker).toBe("cat");
  expect(d[2].text).toBe("Chúc Mừng Sinh Nhật!");
  expect(d[2].speaker).toBe("owner");
});
T("Tổng 12 câu trong DIALOGUES + 'Meow!!' khi hù = 13 (C1-05)", function () {
  var total = 0;
  for (var k in core.DIALOGUES) total += core.DIALOGUES[k].length;
  expect(total).toBe(12);
  // câu 13 "Meow!!" được đặc tả trong W_WALK khi scare — kiểm tra qua simulate
  var s = core.startGame();
  core.setPhase(s, "W_WALK");
  s.player.x = 53; s.player.y = 43; // scare zone 1 (logical ÷3)
  core.updateGame(s, 0.016, {});
  expect(s.dialogue.text).toBe("Meow!!");
});

// ===== 2. Task canonical (§6.1 — AC-2) =====
T("Bảng phase→task đúng §6.1", function () {
  var expect_map = {
    G_INIT: "Đuổi theo con bướm!", G_CHASE: "Đuổi theo con bướm!",
    G_DARK: "Hãy vào nhà!", G_DOOR: "Hãy vào nhà!",
    L_SEARCH: "Tìm chủ nhân ở nhà bếp.",
    K_INIT: "Kiểm tra vết máu!", K_BLOOD: "Kiểm tra vùng tối!", K_CHOICE: "Kiểm tra vùng tối!",
    H_INIT: "Tìm người chủ!",
    H_BLOCK: "Phải đi qua phòng khác!", H_EXIT: "Phải đi qua phòng khác!",
    W_INIT: "Đi qua hành lang.", W_WALK: "Đi qua hành lang.",
    W_DONE: "Đã đến phòng ăn.",
    D_END: "Hoàn thành nhiệm vụ: Tìm chủ nhân."
  };
  for (var p in expect_map) {
    expect(core.PHASES[p].task, "phase " + p).toBe(expect_map[p]);
  }
});

// ===== 3. Chuỗi kịch bản (AC-10/AC-14) =====
T("Bắt đầu: START → G_INIT + dialogue chủ gọi", function () {
  var s = core.startGame();
  expect(s.phase).toBe("G_INIT");
  expect(s.scene).toBe("GARDEN");
  expect(s.player.x).toBe(core.SCENES.GARDEN.spawn.x);
});
T("R-01: dialogue G_INIT hiển thị NGAY sau startGame (câu 1 'Yuniebel! Vào nhà đi!')", function () {
  var s = core.startGame();
  expect(s.dialogue).toBeTruthy();
  expect(s.dialogue.text).toBe("Yuniebel! Vào nhà đi!");
  expect(s.dialogue.speaker).toBe("owner");
  core.updateGame(s, 0.016, {});
  expect(s.dialogue.text).toBe("Yuniebel! Vào nhà đi!");
  for (var i = 0; i < 200; i++) core.updateGame(s, 0.016, {});
  expect(s.dialogue).toBeTruthy();
  expect(s.dialogue.text).toBe("Meow~ Nhưng ngoài này vui quá…");
  expect(s.dialogue.thought).toBe(true);
});
T("R-02: startGame set soundFlags.start (resetStats màn chơi mới)", function () {
  var s = core.startGame();
  expect(s.soundFlags.start).toBe(true);
});
T("Mèo tiến gần cửa (x>260) → bướm xuất hiện + ting", function () {
  var s = core.startGame();
  s.player.x = 263; s.player.y = 50;
  core.updateGame(s, 0.016, {});
  expect(s.butterfly).toBeTruthy();
  expect(s.soundFlags.ting).toBe(true);
});
T("Bắt bướm → G_DARK + darkness ramp 5s (R7)", function () {
  var s = core.startGame();
  s.butterfly = { x: s.player.x + 5, y: s.player.y + 5, wp: 0, stayT: 0, flap: 0 };
  core.updateGame(s, 0.016, {});
  expect(s.phase).toBe("G_DARK");
  expect(s.timers.dark > 0).toBe(true);
  expect(s.darkness).toBe(0);
  for (var i = 0; i < 400; i++) core.updateGame(s, 0.016, {});
  expect(s.phase).toBe("G_DOOR");
});
T("Vào cửa (G_DOOR) → L_SEARCH + dialogue 'Meow? Chủ nhân đâu rồi?'", function () {
  var s = core.startGame();
  core.setPhase(s, "G_DOOR");
  s.player.x = 287; s.player.y = 53;
  core.updateGame(s, 0.016, {});
  expect(s.phase).toBe("L_SEARCH");
  expect(s.dialogue.text).toBe("Meow? Chủ nhân đâu rồi?");
});
T("Phòng khách → cửa bếp → K_INIT", function () {
  var s = core.startGame();
  core.setPhase(s, "L_SEARCH");
  s.player.x = 7; s.player.y = 33;
  core.updateGame(s, 0.016, {});
  expect(s.phase).toBe("K_INIT");
  expect(s.dialogue.text).toBe("Meow… có gì đó lạ…");
});
T("Chạm vết máu → K_BLOOD → hết dialogue → K_CHOICE", function () {
  var s = core.startGame();
  core.setPhase(s, "K_INIT");
  s.player.x = 63; s.player.y = 73;
  core.updateGame(s, 0.016, {});
  expect(s.phase).toBe("K_BLOOD");
  expect(s.dialogue.text).toBe("Meow?! Đây là gì vậy?");
  for (var i = 0; i < 10; i++) core.updateGame(s, 0.016, {});
  s.dialogue = null; s.dialogueQueue = [];
  s.player.x = 13; s.player.y = 13;
  core.updateGame(s, 0.016, {});
  expect(s.phase).toBe("K_CHOICE");
});
T("Chọn 2 → GAME_OVER + swoosh + painMeow (AC-10)", function () {
  var s = core.startGame();
  core.setPhase(s, "K_CHOICE");
  core.updateGame(s, 0.016, { choice2: true });
  expect(s.phase).toBe("GAME_OVER");
  expect(s.choice).toBe(2);
  expect(s.soundFlags.swoosh).toBe(true);
  expect(s.soundFlags.painMeow).toBe(true);
});
T("Chọn 1 → H_INIT + rush (AC-10)", function () {
  var s = core.startGame();
  core.setPhase(s, "K_CHOICE");
  core.updateGame(s, 0.016, { choice1: true });
  expect(s.phase).toBe("H_INIT");
  expect(s.choice).toBe(1);
  expect(s.soundFlags.rush).toBe(true);
});
T("H_INIT hết dialogue → H_BLOCK + ma đẩy lùi + đổi task (C1-14)", function () {
  var s = core.startGame();
  core.setPhase(s, "H_INIT");
  s.dialogue = null;
  s.dialogueQueue = [];
  core.updateGame(s, 0.016, {});
  expect(s.phase).toBe("H_BLOCK");
  s.player.x = 143; s.player.y = 50;
  var x0 = s.player.x;
  core.updateGame(s, 0.016, {});
  expect(s.player.x < x0).toBe(true);
  expect(s.ghostBlocked).toBe(true);
  expect(core.PHASES[s.phase].task).toBe("Phải đi qua phòng khác!");
});
T("Cửa phụ trái → W_INIT (không deadlock — C2-03)", function () {
  var s = core.startGame();
  core.setPhase(s, "H_EXIT");
  s.player.x = 3; s.player.y = 33;
  core.updateGame(s, 0.016, {});
  expect(s.phase).toBe("W_INIT");
  expect(s.scene).toBe("HALLWAY");
});
T("5 scare zone → W_DONE + 'Meow!!' mỗi lần (AC-8)", function () {
  var s = core.startGame();
  core.setPhase(s, "W_WALK");
  var zones = core.SCENES.HALLWAY.scareZones;
  for (var i = 0; i < zones.length; i++) {
    s.player.x = zones[i].x + 10; s.player.y = zones[i].y + 10;
    core.updateGame(s, 0.016, {});
    if (i < 4) {
      expect(s.phase).toBe("W_WALK");
      expect(s.scareActive).toBe(i + 1);
      expect(s.dialogue.text).toBe("Meow!!");
      for (var j = 0; j < 120; j++) core.updateGame(s, 0.016, {});
      expect(s.scareActive).toBe(0);
    }
  }
  expect(s.scareCount).toBe(5);
  expect(s.phase).toBe("W_DONE");
});
T("W_DONE → cửa → D_END + 3 câu thoại sinh nhật (AC-9)", function () {
  var s = core.startGame();
  core.setPhase(s, "W_DONE");
  s.player.x = 303; s.player.y = 43;
  core.updateGame(s, 0.016, {});
  expect(s.phase).toBe("D_END");
  expect(s.dialogue.text).toBe("Happy Birthday Yuniebel!");
});
T("D_END hết thoại + 3s → END + bell (R6)", function () {
  var s = core.startGame();
  core.setPhase(s, "D_END");
  s.dialogue = null; s.dialogueQueue = [];
  for (var i = 0; i < 300; i++) core.updateGame(s, 0.016, {});
  expect(s.phase).toBe("END");
  expect(s.soundFlags.bell).toBe(true);
});
T("GAME OVER → START lại → G_INIT (reset)", function () {
  var s = core.startGame();
  core.setPhase(s, "GAME_OVER");
  core.updateGame(s, 0.016, { start: true });
  expect(s.phase).toBe("G_INIT");
  expect(s.dialogue).toBeTruthy();
});

// ===== 4. Collision (AC-14) =====
T("Không xuyên tường nhà (GARDEN)", function () {
  var s = core.startGame();
  s.player.x = 263; s.player.y = 30;
  var x0 = s.player.x;
  core.updateGame(s, 0.016, { right: true });
  expect(s.player.x <= x0 + 2).toBe(true);
});
T("Không ra ngoài biên map", function () {
  var s = core.startGame();
  s.player.x = 0; s.player.y = 0;
  core.updateGame(s, 0.1, { left: true, up: true });
  expect(s.player.x >= 0 && s.player.y >= 0).toBe(true);
});
