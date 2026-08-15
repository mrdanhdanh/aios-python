/* core.js — AIOS Game "Yuniebel's Cat" (TASK-078, viết lại từ đầu)
 * Logic thuần (browser + Node test). UMD: module.exports khi Node, AiosCore khi browser.
 * KHÔNG dùng window/document/rAF. MỌI animation dựa state.time (R1) — freeze đóng băng state.time.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.AiosCore = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ====== Hằng số (logical grid — 1 đơn vị = 1 pixel sprite, ×3 → canvas 480×270) ======
  var WALK_SPEED = 40;         // px/s mèo (logical)
  var BUTTERFLY_SPEED = 20;    // px/s bướm (waypoint cố định — C2-07)
  var MAX_DT = 0.05;           // clamp delta time (50ms)
  var PW = 16, PH = 16;        // player sprite (16×16 logical)
  var HBX = 3, HBW = 10;       // hitbox lệch (x+3, y+2, 10x12)
  var HBY = 2, HBH = 12;
  var KNOCKBACK = 13;          // px đẩy lùi cửa ma (logical)
  var KNOCKBACK_CD = 1.5;      // giây
  var DARK_RECT = { x: 7, y: 7, w: 31, h: 33 }; // vùng tối bếp (logical — khớp sprites.js)
  var BUTTERFLY_CATCH = 4;     // px bán kính bắt bướm (cosmetic — butterflyHit dùng bbox 8/16)
  var BUTTERFLY_STAY = 13;     // px bán kính "đứng yên bắt"
  var BUTTERFLY_STAY_T = 1.0;  // giây đứng trong vùng bán kính
  var DARK_RAMP = 5.0;         // giây tối dần sau bắt bướm (R7)

  // ====== Scenes: map + walls + zones ======
  // zone: {id, x, y, w, h, phases:[...]} — action xử lý trong updateGame
  var SCENES = {
    GARDEN: {
      w: 320, h: 90,
      spawn: { x: 107, y: 70 },
      butterflyWp: [ { x: 167, y: 40 }, { x: 217, y: 30 }, { x: 180, y: 63 } ],
      walls: [
        { x: 267, y: 7, w: 53, h: 43 },   // thân nhà (tới y=50)
        { x: 67, y: 62, w: 8, h: 5 },     // bụi cây 1
        { x: 117, y: 33, w: 7, h: 5 },    // bụi cây 2
        { x: 207, y: 85, w: 9, h: 4 },    // bụi cây 3 (sát mép dưới — không chặn đường chính y=70)
        { x: 13, y: 50, w: 7, h: 4 },     // bụi cây 4
        { x: 230, y: 13, w: 6, h: 23 }    // cây lớn
      ],
      zones: [
        { id: "door", x: 284, y: 48, w: 11, h: 20, phases: ["G_INIT", "G_DOOR"] }
      ]
    },
    LIVING: {
      w: 160, h: 90,
      spawn: { x: 113, y: 63 },
      walls: [
        { x: 10, y: 53, w: 30, h: 15 },   // sofa
        { x: 63, y: 67, w: 23, h: 4 },    // bàn trà
        { x: 127, y: 70, w: 10, h: 17 }   // kệ
      ],
      zones: [
        { id: "door_kitchen", x: 3, y: 30, w: 11, h: 20, phases: ["L_SEARCH"] }
      ]
    },
    KITCHEN: {
      w: 160, h: 90,
      spawn: { x: 80, y: 73 },
      walls: [
        { x: 100, y: 47, w: 30, h: 15 },  // bàn bếp
        { x: 127, y: 7, w: 33, h: 43 }    // tủ bếp phải
      ],
      zones: [
        { id: "blood", x: 50, y: 78, w: 40, h: 8, phases: ["K_INIT", "K_BLOOD"] },
        { id: "dark", x: DARK_RECT.x, y: DARK_RECT.y, w: DARK_RECT.w, h: DARK_RECT.h, phases: ["K_BLOOD"] },
        { id: "door_out", x: 149, y: 43, w: 11, h: 20, phases: ["K_CHOICE"] }
      ]
    },
    HAUNTED: {
      w: 160, h: 90,
      spawn: { x: 90, y: 63 },
      walls: [
        { x: 10, y: 53, w: 30, h: 15 },   // sofa cũ
        { x: 67, y: 68, w: 20, h: 4 }     // bàn
      ],
      zones: [
        { id: "door_front", x: 143, y: 33, w: 15, h: 33, phases: ["H_INIT", "H_BLOCK", "H_EXIT"] },
        { id: "door_side", x: 2, y: 30, w: 11, h: 20, phases: ["H_BLOCK", "H_EXIT"] }
      ]
    },
    HALLWAY: {
      w: 320, h: 90,
      spawn: { x: 20, y: 45 },
      walls: [
        { x: 0, y: 33, w: 9, h: 23 }      // cửa vào đóng (one-way)
      ],
      scareZones: [                       // 5 vị trí hù (C1-08: scare1..5)
        { x: 47, y: 33, w: 30, h: 20 },
        { x: 100, y: 33, w: 30, h: 20 },
        { x: 153, y: 33, w: 30, h: 20 },
        { x: 207, y: 33, w: 30, h: 20 },
        { x: 260, y: 33, w: 30, h: 20 }
      ],
      zones: [
        { id: "door_dining", x: 302, y: 33, w: 14, h: 20, phases: ["W_WALK", "W_DONE"] }
      ]
    },
    BIRTHDAY: {
      w: 160, h: 90,
      spawn: { x: 80, y: 67 },
      walls: [
        { x: 47, y: 47, w: 67, h: 20 }   // bàn bánh kem
      ],
      zones: []
    }
  };

  // ====== Phase info: task text canonical (§6.1) + input lock ======
  var PHASES = {
    TITLE:      { scene: "TITLE",     task: "", lock: false },
    G_INIT:     { scene: "GARDEN",    task: "Đuổi theo con bướm!", lock: false },
    G_CHASE:    { scene: "GARDEN",    task: "Đuổi theo con bướm!", lock: false },
    G_DARK:     { scene: "GARDEN",    task: "Hãy vào nhà!", lock: false },
    G_DOOR:     { scene: "GARDEN",    task: "Hãy vào nhà!", lock: false },
    L_SEARCH:   { scene: "LIVING",    task: "Tìm chủ nhân ở nhà bếp.", lock: false },
    K_INIT:     { scene: "KITCHEN",   task: "Kiểm tra vết máu!", lock: false },
    K_BLOOD:    { scene: "KITCHEN",   task: "Kiểm tra vết máu!", lock: false },
    K_CHOICE:   { scene: "KITCHEN",   task: "Kiểm tra vết máu!", lock: false },
    H_INIT:     { scene: "HAUNTED",   task: "Tìm người chủ!", lock: false },
    H_BLOCK:    { scene: "HAUNTED",   task: "Phải đi qua phòng khác!", lock: false },
    H_EXIT:     { scene: "HAUNTED",   task: "Phải đi qua phòng khác!", lock: false },
    W_INIT:     { scene: "HALLWAY",   task: "Đi qua hành lang.", lock: false },
    W_WALK:     { scene: "HALLWAY",   task: "Đi qua hành lang.", lock: false },
    W_DONE:     { scene: "HALLWAY",   task: "Đã đến phòng ăn.", lock: false },
    D_END:      { scene: "BIRTHDAY",  task: "Hoàn thành nhiệm vụ: Tìm chủ nhân.", lock: false },
    GAME_OVER:  { scene: "GAMEOVER",  task: "", lock: true },
    END:        { scene: "END",       task: "", lock: true }
  };

  // ====== Dialogue: 13 câu canonical (khớp 100% brief-scenario.md — AC-1) ======
  // {text, dur, thought, speaker} — tự advance theo dur (C2-02/R5)
  var DIALOGUES = {
    G_INIT: [
      { text: "Yuniebel! Vào nhà đi!", dur: 2.5, thought: false, speaker: "owner" },
      { text: "Meow~ Nhưng ngoài này vui quá…", dur: 2.5, thought: true, speaker: "cat" }
    ],
    L_SEARCH: [
      { text: "Meow? Chủ nhân đâu rồi?", dur: 2.5, thought: true, speaker: "cat" }
    ],
    K_INIT: [
      { text: "Meow… có gì đó lạ…", dur: 2.0, thought: true, speaker: "cat" }
    ],
    K_BLOOD: [
      { text: "Meow?! Đây là gì vậy?", dur: 2.2, thought: true, speaker: "cat" },
      { text: "Đến đây đi… Meow…", dur: 2.5, thought: false, speaker: "dark" }
    ],
    H_INIT: [
      { text: "Meow… căn phòng này… khác rồi…", dur: 2.4, thought: true, speaker: "cat" },
      { text: "Không được rời đi…", dur: 2.4, thought: false, speaker: "ghost" }
    ],
    W_INIT: [
      { text: "Meow… mình phải đi tiếp…", dur: 2.4, thought: true, speaker: "cat" }
    ],
    D_END: [
      { text: "Happy Birthday Yuniebel!", dur: 2.5, thought: false, speaker: "owner" },
      { text: "Meow~", dur: 1.5, thought: true, speaker: "cat" },
      { text: "Chúc Mừng Sinh Nhật!", dur: 3.0, thought: false, speaker: "owner" }
    ]
  };

  // ====== Helpers ======
  function clamp(v, min, max) { return v < min ? min : (v > max ? max : v); }
  function aabb(x1, y1, w1, h1, x2, y2, w2, h2) {
    return x1 < x2 + w2 && x1 + w1 > x2 && y1 < y2 + h2 && y1 + h1 > y2;
  }
  function rectsOverlap(r1, r2) {
    return aabb(r1.x, r1.y, r1.w, r1.h, r2.x, r2.y, r2.w, r2.h);
  }
  function ph(state) { return PHASES[state.phase]; }

  // ====== State ======
  function resetGame() {
    return {
      scene: "TITLE",
      phase: "TITLE",
      player: { x: 240, y: 120, dir: 1, moving: false },
      darkness: 0,            // 0..1 — GARDEN tối dần theo DARK_RAMP
      scareCount: 0,          // 0..5 (hành lang)
      scareActive: 0,         // 0 = không; 1..5 = kiểu hù đang hiển thị (mapping §6.2)
      ghostBlocked: false,    // đã bị ma đẩy lần đầu → task đổi vĩnh viễn (C1-14)
      knockbackCd: 0,
      fired: {},              // "phase:zone" → true (fire-once)
      timers: {},
      butterfly: null,        // {x, y, wp, stayT}
      dialogue: null,         // {text, dur, until, thought, speaker}
      dialogueQueue: [],      // hàng đợi câu thoại tuần tự
      choice: null,           // 1 | 2
      scareMsgIdx: 0,
      scareTimer: 0,          // R-04: hết hạn hiển thị scare
      flash: 0,               // R-04: flash jump scare 0..1
      flashUntil: 0,
      soundFlags: {},         // cờ âm thanh → game.js phát 1 lần rồi xóa
      time: 0,
      frozen: false,          // R1: freeze — update không tiến triển state.time
      endTimer: 0             // D_END → END sau 3s (R6)
    };
  }

  function startGame() {
    var s = resetGame();
    s.scene = "GARDEN";
    s.phase = "G_INIT";
    s.player = { x: SCENES.GARDEN.spawn.x, y: SCENES.GARDEN.spawn.y, dir: 1, moving: false };
    s.soundFlags.intro = true;
    s.soundFlags.start = true; // R-02: resetStats màn chơi mới
    pushDialogue(s, "G_INIT");
    nextDialogue(s); // R-01: hiển thị câu đầu ngay
    return s;
  }

  function pushDialogue(state, key) {
    var list = DIALOGUES[key];
    if (!list) return;
    state.dialogueQueue = list.map(function (d) { return { text: d.text, dur: d.dur, thought: d.thought, speaker: d.speaker }; });
    state.dialogue = null;
  }

  function nextDialogue(state) {
    if (state.dialogueQueue.length > 0) {
      var d = state.dialogueQueue.shift();
      state.dialogue = { text: d.text, dur: d.dur, thought: d.thought, speaker: d.speaker, until: state.time + d.dur };
    } else {
      state.dialogue = null;
    }
  }

  function setPhase(state, phase, extra) {
    state.phase = phase;
    var info = PHASES[phase];
    if (info && info.scene) state.scene = info.scene;
    if (extra) for (var k in extra) state[k] = extra[k];
  }

  function zoneKey(phase, zoneId) { return phase + ":" + zoneId; }

  // ====== Collision ======
  function hitboxRect(state) {
    var p = state.player;
    return { x: p.x + HBX, y: p.y + HBY, w: HBW, h: HBH };
  }

  function collides(state, x, y) {
    var hb = { x: x + HBX, y: y + HBY, w: HBW, h: HBH };
    var sc = SCENES[state.scene];
    if (!sc) return false;
    if (hb.x < 0 || hb.y < 0 || hb.x + hb.w > sc.w || hb.y + hb.h > sc.h) return true; // biên map
    for (var i = 0; i < sc.walls.length; i++) {
      if (rectsOverlap(hb, sc.walls[i])) return true;
    }
    // vùng tối bếp = tường vô hình trước K_BLOOD (giữ mèo khỏi bước vào tối sớm)
    if (state.scene === "KITCHEN" && state.phase !== "K_BLOOD" && state.phase !== "K_CHOICE") {
      if (rectsOverlap(hb, DARK_RECT)) return true;
    }
    return false;
  }

  function movePlayer(state, dx, dy) {
    var p = state.player;
    var sc = SCENES[state.scene];
    var nx = p.x + dx;
    if (!collides(state, nx, p.y)) p.x = nx;
    var ny = p.y + dy;
    if (!collides(state, p.x, ny)) p.y = ny;
    if (sc) {
      p.x = clamp(p.x, 0, sc.w - PW);
      p.y = clamp(p.y, 0, sc.h - PH);
    }
    if (dx !== 0) p.dir = dx > 0 ? 1 : -1;
    p.moving = (dx !== 0 || dy !== 0);
  }

  function knockback(state, dx) {
    movePlayer(state, dx, 0);
    state.knockbackCd = KNOCKBACK_CD;
  }

  // ====== Trigger zones ======
  function checkZones(state) {
    var sc = SCENES[state.scene];
    if (!sc || !sc.zones) return [];
    var hb = hitboxRect(state);
    var fired = [];
    for (var i = 0; i < sc.zones.length; i++) {
      var z = sc.zones[i];
      if (z.phases.indexOf(state.phase) === -1) continue;
      var key = zoneKey(state.phase, z.id);
      if (state.fired[key]) continue;
      if (rectsOverlap(hb, z)) {
        state.fired[key] = true;
        fired.push(z);
      }
    }
    return fired;
  }

  // ====== Bướm AI (C2-07): waypoint cố định, bắt khi chạm/đứng yên ======
  function updateButterfly(state, dt) {
    var b = state.butterfly;
    if (!b) return;
    var sc = SCENES.GARDEN;
    var wp = sc.butterflyWp[b.wp % sc.butterflyWp.length];
    var dx = wp.x - b.x, dy = wp.y - b.y;
    var dist = Math.sqrt(dx * dx + dy * dy);
    var vx = 0, vy = 0;
    if (dist > 6) {
      vx = (dx / dist) * BUTTERFLY_SPEED;
      vy = (dy / dist) * BUTTERFLY_SPEED;
    } else {
      b.wp = (b.wp + 1) % sc.butterflyWp.length;
      b.stayT = 0;
    }
    b.x = clamp(b.x + vx * dt, 8, sc.w - 20);
    b.y = clamp(b.y + vy * dt, 8, sc.h - 20);
    // flap
    b.flap = state.time * 8;
    // R-07: tiếng vỗ cánh thỉnh thoảng
    if (Math.floor(state.time * 4) % 8 === 0) state.soundFlags.flutter = true;
    // R-10: stayT dùng dt thật (đứng yên trong vòng 40px ≥1s)
    var p = state.player;
    var pd = Math.sqrt((b.x - p.x) * (b.x - p.x) + (b.y - p.y) * (b.y - p.y));
    if (pd < BUTTERFLY_STAY) {
      b.stayT = (b.stayT || 0) + dt;
      if (b.stayT >= BUTTERFLY_STAY_T) { b.stayT = 0; b.caught = true; }
    } else {
      b.stayT = 0;
    }
  }

  function butterflyHit(state) {
    var b = state.butterfly;
    if (!b) return false;
    if (b.caught) return true; // R-10: đứng yên đủ lâu → bắt
    var p = state.player;
    var cx = b.x, cy = b.y;
    if (aabb(p.x + HBX, p.y + HBY, HBW, HBH, cx - 8, cy - 8, 16, 16)) return true;
    return false;
  }

  // ====== Main update ======
  function updateGame(state, dt, input) {
    if (state.frozen) return; // R1 — freeze: không tiến triển
    dt = clamp(dt, 0, MAX_DT);
    state.time += dt;

    // R-01: queue còn → hiện câu tiếp
    if (!state.dialogue && state.dialogueQueue.length > 0) nextDialogue(state);

    // R-04: scare hết hạn sau ~1.5s
    if (state.scareActive && state.scareTimer > 0) {
      state.scareTimer -= dt;
      if (state.scareTimer <= 0) { state.scareActive = 0; state.scareTimer = 0; }
    }
    if (state.flashUntil && state.time >= state.flashUntil) { state.flash = 0; state.flashUntil = 0; }

    // dialogue tự advance theo dur
    if (state.dialogue && state.time >= state.dialogue.until) {
      nextDialogue(state);
    }

    if (state.knockbackCd > 0) state.knockbackCd -= dt;
    for (var tk in state.timers) state.timers[tk] -= dt;

    // Hành động toàn cục
    if (input.start) {
      if (state.scene === "TITLE" || state.scene === "GAMEOVER" || state.scene === "END") {
        var ns = startGame();
        for (var k in state) delete state[k];
        for (k in ns) state[k] = ns[k];
        return;
      }
      // Space/Enter advance hội thoại nhanh
      if (state.dialogue) { nextDialogue(state); return; }
    }

    var phinfo = ph(state);
    var locked = phinfo ? phinfo.lock : false;
    var dx = 0, dy = 0;
    if (!locked) {
      if (input.up) dy -= 1;
      if (input.down) dy += 1;
      if (input.left) dx -= 1;
      if (input.right) dx += 1;
      if (dx !== 0 || dy !== 0) {
        var len = Math.sqrt(dx * dx + dy * dy);
        movePlayer(state, (dx / len) * WALK_SPEED * dt, (dy / len) * WALK_SPEED * dt);
      } else {
        state.player.moving = false;
      }
    }

    var zones = checkZones(state);
    var i, z;

    switch (state.phase) {
      case "TITLE":
        break;

      case "G_INIT":
        // bướm xuất hiện khi mèo tiến gần cửa (x > 260 — C2-07/R12), trừ khi đã bắt
        if (state.player.x > 260 && !state.butterfly) {
          state.butterfly = { x: 233, y: 47, wp: 0, stayT: 0, flap: 0 };
          state.soundFlags.ting = true;
        }
        if (state.butterfly) {
          updateButterfly(state, dt);
          if (butterflyHit(state)) {
            state.butterfly = null;
            setPhase(state, "G_DARK");
            state.darkness = 0;
            state.timers.dark = DARK_RAMP;
            state.soundFlags.darkStart = true;
          }
        }
        break;

      case "G_CHASE":
        if (state.butterfly) {
          updateButterfly(state, dt);
          if (butterflyHit(state)) {
            state.butterfly = null;
            setPhase(state, "G_DARK");
            state.darkness = 0;
            state.timers.dark = DARK_RAMP;
            state.soundFlags.darkStart = true;
          }
        }
        break;

      case "G_DARK":
        // darkness ramp 5s (R7)
        state.darkness = clamp(1 - (state.timers.dark || 0) / DARK_RAMP, 0, 1);
        if (state.darkness >= 1) setPhase(state, "G_DOOR");
        break;

      case "G_DOOR":
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door") {
            setPhase(state, "L_SEARCH");
            state.player.x = SCENES.LIVING.spawn.x;
            state.player.y = SCENES.LIVING.spawn.y;
            pushDialogue(state, "L_SEARCH");
            nextDialogue(state);
            state.soundFlags.clockTick = true; // R-06: đúng tên SFX
          }
        }
        break;

      case "L_SEARCH":
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door_kitchen") {
            setPhase(state, "K_INIT");
            state.player.x = SCENES.KITCHEN.spawn.x;
            state.player.y = SCENES.KITCHEN.spawn.y;
            pushDialogue(state, "K_INIT");
            nextDialogue(state);
          }
        }
        break;

      case "K_INIT":
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "blood") {
            setPhase(state, "K_BLOOD");
            state.soundFlags.drip = true;
            pushDialogue(state, "K_BLOOD");
            nextDialogue(state);
            state.soundFlags.whisper = true;
          }
        }
        break;

      case "K_BLOOD":
        // đứng cạnh vết máu: hết dialogue → vùng tối thì thầm → K_CHOICE
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "dark") {
            setPhase(state, "K_CHOICE");
            state.soundFlags.whisperFar = true;
          }
        }
        break;

      case "K_CHOICE":
        if (input.choice1) {
          state.choice = 1;
          state.soundFlags.rush = true;
          setPhase(state, "H_INIT");
          state.player.x = SCENES.HAUNTED.spawn.x;
          state.player.y = SCENES.HAUNTED.spawn.y;
          pushDialogue(state, "H_INIT");
          nextDialogue(state);
          state.soundFlags.whoosh = true;
        } else if (input.choice2) {
          state.choice = 2;
          state.soundFlags.swoosh = true;
          state.soundFlags.painMeow = true;
          setPhase(state, "GAME_OVER");
        }
        break;

      case "H_INIT":
        // hết dialogue → H_BLOCK (ma xuất hiện + whoosh)
        if (!state.dialogue) {
          setPhase(state, "H_BLOCK");
          state.soundFlags.whoosh = true;
          state.soundFlags.scaredMeow = true;
        }
        break;

      case "H_BLOCK":
        // cố đi ra cửa chính (phải) → bị ma đẩy lùi; lần đầu đổi task vĩnh viễn
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door_front" && state.knockbackCd <= 0) {
            knockback(state, -KNOCKBACK);
            state.knockbackCd = KNOCKBACK_CD;
            if (!state.ghostBlocked) {
              state.ghostBlocked = true;
              state.soundFlags.creak = true;
              state.soundFlags.scaredMeow = true;
            }
            delete state.fired["H_BLOCK:door_front"]; // R-11: đẩy lùi lặp lại (mỗi cooldown)
          }
          // cửa phụ trái vẫn thoát được (tránh deadlock — C2-03)
          if (zones[i].id === "door_side") {
            setPhase(state, "W_INIT");
            state.player.x = SCENES.HALLWAY.spawn.x;
            state.player.y = SCENES.HALLWAY.spawn.y;
            pushDialogue(state, "W_INIT");
            nextDialogue(state);
          }
        }
        break;

      case "H_EXIT":
        // cửa chính vẫn bị ma chặn (knockback, không đổi task nữa — C1-14)
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door_front" && state.knockbackCd <= 0) {
            knockback(state, -KNOCKBACK);
          }
        }
        // đi qua cửa phụ (trái) → hành lang
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door_side") {
            setPhase(state, "W_INIT");
            state.player.x = SCENES.HALLWAY.spawn.x;
            state.player.y = SCENES.HALLWAY.spawn.y;
            pushDialogue(state, "W_INIT");
            nextDialogue(state);
          }
        }
        break;

      case "W_INIT":
        if (!state.dialogue) setPhase(state, "W_WALK");
        break;

      case "W_WALK":
        // 5 scare zone (fire-once)
        var sc = SCENES.HALLWAY;
        var hb = hitboxRect(state);
        for (i = 0; i < sc.scareZones.length; i++) {
          z = sc.scareZones[i];
          var zkey = "scare" + (i + 1);
          if (state.fired[zkey]) continue;
          if (rectsOverlap(hb, z)) {
            state.fired[zkey] = true;
            state.scareCount++;
            state.scareActive = i + 1;   // mapping §6.2
            state.scareTimer = 1.5;      // R-04: hết hạn sau 1.5s
            state.flash = 0.5;           // R-04: flash jump scare
            state.flashUntil = state.time + 0.3;
            // "Meow!!" — câu thoại thứ 13 (brief: mỗi lần bị hù)
            state.dialogue = { text: "Meow!!", dur: 1.0, thought: true, speaker: "cat", until: state.time + 1.0 };
            state.soundFlags.jumpscare = true;
            state.soundFlags.scaredMeow = true;
            if (state.scareCount >= 5) {
              setPhase(state, "W_DONE");
              state.soundFlags.warm = true;
            }
            break;
          }
        }
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door_dining") {
            setPhase(state, "D_END");
            state.player.x = SCENES.BIRTHDAY.spawn.x;
            state.player.y = SCENES.BIRTHDAY.spawn.y;
            pushDialogue(state, "D_END");
            nextDialogue(state);
            state.soundFlags.happyMeow = true;
            state.soundFlags.candle = true;
          }
        }
        break;

      case "W_DONE":
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door_dining") {
            setPhase(state, "D_END");
            state.player.x = SCENES.BIRTHDAY.spawn.x;
            state.player.y = SCENES.BIRTHDAY.spawn.y;
            pushDialogue(state, "D_END");
            nextDialogue(state);
            state.soundFlags.happyMeow = true;
            state.soundFlags.candle = true;
          }
        }
        break;

      case "D_END":
        // hết 3 câu thoại + 3s → END (R6)
        if (!state.dialogue && !state.dialogueQueue.length) {
          state.endTimer += dt;
          if (state.endTimer >= 3.0) {
            setPhase(state, "END");
            state.soundFlags.bell = true;
            state.soundFlags.sparkle = true;
          }
        } else {
          state.endTimer = 0;
        }
        break;

      case "GAME_OVER":
      case "END":
        break;
    }
  }

  // ====== Debug API (chỉ active khi URL ?test=1 — game.js gate, C1-15) ======
  function makeDebug(s) {
    return {
      setPhase: function (p) { setPhase(s, p); },
      setPlayer: function (x, y) { s.player.x = x; s.player.y = y; },
      setDarkness: function (v) { s.darkness = clamp(v, 0, 1); },
      setTimers: function (o) { for (var k in o) s.timers[k] = o[k]; },
      setScareCount: function (n) { s.scareCount = clamp(n, 0, 5); },
      setScareZone: function (n) { s.scareActive = n ? clamp(n, 1, 5) : 0; },
      setMessage: function (text, until) {
        s.dialogue = { text: text, dur: until || 999, thought: false, speaker: "owner", until: s.time + (until || 999) };
      },
      setChoice: function (n) { s.choice = n; },
      setButterfly: function (x, y) {
        s.butterfly = { x: x == null ? 233 : x, y: y == null ? 50 : y, wp: 0, stayT: 0, flap: 0 };
      },
      freeze: function (v) { s.frozen = !!v; }
    };
  }

  // ====== Export ======
  function createGame() {
    var s = resetGame();
    return {
      state: s,
      debug: makeDebug(s),
      update: function (dt, input) { updateGame(s, dt, input); },
      getTask: function () { return PHASES[s.phase].task; },
      getPhase: function () { return s.phase; },
      reset: function () {
        var ns = resetGame();
        for (var k in s) delete s[k];
        for (k in ns) s[k] = ns[k];
      }
    };
  }

  return {
    resetGame: resetGame,
    startGame: startGame,
    updateGame: updateGame,
    movePlayer: movePlayer,
    collides: collides,
    checkZones: checkZones,
    updateButterfly: updateButterfly,
    butterflyHit: butterflyHit,
    setPhase: setPhase,
    nextDialogue: nextDialogue,
    createGame: createGame,
    PHASES: PHASES,
    DIALOGUES: DIALOGUES,
    SCENES: SCENES,
    WALK_SPEED: WALK_SPEED,
    BUTTERFLY_SPEED: BUTTERFLY_SPEED,
    MAX_DT: MAX_DT,
    HBX: HBX, HBW: HBW, HBY: HBY, HBH: HBH,
    PW: PW, PH: PH,
    DARK_RECT: DARK_RECT,
    KNOCKBACK: KNOCKBACK
  };
});
