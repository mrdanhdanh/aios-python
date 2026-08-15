/* core.js — AIOS Game "Yuniebel" — logic thuần (browser + Node test)
 * KHÔNG dùng window/document/rAF. UMD: module.exports khi Node, AiosCore khi browser.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.AiosCore = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ====== Hằng số ======
  var WALK_SPEED = 120;        // px/s mèo
  var BUTTERFLY_SPEED = 85;    // px/s bướm khi tránh mèo
  var MAX_DT = 0.05;           // clamp delta time (50ms)
  var LIGHT_RADIUS = 90;       // bán kính vùng sáng quanh mèo (cảnh tối)
  var PW = 16, PH = 16;        // player sprite
  var HBX = 3, HBW = 10;       // hitbox lệch (x+3, y+2, 10x12)
  var HBY = 2, HBH = 12;
  var DARK_RECT = { x: 20, y: 20, w: 92, h: 100 }; // vùng tối bếp
  var KNOCKBACK = 40;          // px đẩy lùi cửa trước cảnh ma
  var KNOCKBACK_CD = 1.5;      // giây

  // ====== Scenes: map + walls + zones ======
  // zone: {id, x, y, w, h, phases:[...], action} — action xử lý trong updateGame
  var SCENES = {
    GARDEN: {
      w: 960, h: 270,
      spawn: { x: 420, y: 200 },
      butterfly: { x: 700, y: 150 },
      walls: [
        { x: 760, y: 30, w: 200, h: 132 },   // thân nhà trên (tới y=162)
        { x: 760, y: 162, w: 74, h: 12 },    // nhà trái cửa (mặt dưới)
        { x: 866, y: 162, w: 94, h: 12 },    // nhà phải cửa (mặt dưới)
        { x: 200, y: 185, w: 24, h: 14 },    // bụi cây 1
        { x: 350, y: 100, w: 22, h: 14 },    // bụi cây 2
        { x: 560, y: 215, w: 26, h: 14 },    // bụi cây 3 (sát mép dưới — đường chính thoáng)
        { x: 40, y: 150, w: 20, h: 12 },     // bụi cây 4
        { x: 660, y: 40, w: 18, h: 70 }      // cây lớn
      ],
      zones: [
        { id: "door", x: 834, y: 150, w: 32, h: 40, phases: ["G_INIT", "G_DOOR"] }
      ]
    },
    LIVING: {
      w: 480, h: 270,
      spawn: { x: 420, y: 190 },
      walls: [
        { x: 30, y: 160, w: 90, h: 40 },    // sofa
        { x: 200, y: 195, w: 60, h: 12 },   // bàn trà
        { x: 380, y: 210, w: 30, h: 50 }    // kệ TV (sát tường dưới — không chặn đường chính)
      ],
      zones: [
        { id: "door_kitchen", x: 18, y: 85, w: 34, h: 46, phases: ["L_SEARCH"] },
        { id: "door_out", x: 428, y: 130, w: 34, h: 52, phases: [] }
      ]
    },
    KITCHEN: {
      w: 480, h: 270,
      spawn: { x: 240, y: 240 },
      walls: [
        { x: 300, y: 140, w: 80, h: 45 },   // bàn bếp
        { x: 380, y: 20, w: 100, h: 130 }   // tủ bếp phải
      ],
      zones: [
        { id: "blood", x: 350, y: 235, w: 50, h: 20, phases: ["K_INIT"] },
        { id: "dark", x: DARK_RECT.x, y: DARK_RECT.y, w: DARK_RECT.w, h: DARK_RECT.h, phases: ["K_CHOICE", "K_OBEY"] }
      ]
    },
    HAUNTED: {
      w: 480, h: 270,
      spawn: { x: 240, y: 190 },
      walls: [
        { x: 30, y: 160, w: 90, h: 40 },   // sofa
        { x: 200, y: 205, w: 60, h: 12 }   // bàn (sát dưới — không chặn đường lên cửa)
      ],
      zones: [
        { id: "door_front", x: 428, y: 120, w: 34, h: 60, phases: ["H_SEARCH"] },
        { id: "door_hall", x: 205, y: 16, w: 40, h: 34, phases: ["H_SEARCH"] }
      ]
    },
    HALLWAY: {
      w: 960, h: 270,
      spawn: { x: 60, y: 135 },
      walls: [
        { x: 0, y: 100, w: 28, h: 70 }     // cửa vào đóng (one-way)
      ],
      zones: [
        { id: "scare1", x: 140, y: 100, w: 90, h: 60, phases: ["W_WALK"] },
        { id: "scare2", x: 300, y: 100, w: 90, h: 60, phases: ["W_WALK"] },
        { id: "scare3", x: 460, y: 100, w: 90, h: 60, phases: ["W_WALK"] },
        { id: "scare4", x: 620, y: 100, w: 90, h: 60, phases: ["W_WALK"] },
        { id: "scare5", x: 780, y: 100, w: 90, h: 60, phases: ["W_WALK"] },
        { id: "door_dining", x: 905, y: 100, w: 42, h: 60, phases: ["W_DONE"] }
      ]
    },
    DINING: {
      w: 480, h: 270,
      spawn: { x: 60, y: 210 },
      walls: [
        { x: 150, y: 120, w: 180, h: 55 }  // bàn ăn
      ],
      zones: [
        { id: "approach", x: 170, y: 195, w: 140, h: 45, phases: ["D_APPROACH"] }
      ]
    }
  };

  // ====== Phase info: task text + input lock ======
  var PHASES = {
    TITLE:      { scene: "TITLE",   task: "", lock: false },
    G_INIT:     { scene: "GARDEN",  task: "Nghe lời chủ — vào nhà", lock: false },
    G_BUTTERFLY:{ scene: "GARDEN",  task: "Bướm kìa! Đuổi theo con bướm!", lock: false },
    G_CHASE:    { scene: "GARDEN",  task: "Đuổi theo con bướm!", lock: false },
    G_DARK:     { scene: "GARDEN",  task: "Trời tối rồi — nhanh vào nhà!", lock: false },
    G_DOOR:     { scene: "GARDEN",  task: "Vào nhà ngay!", lock: false },
    L_SEARCH:   { scene: "LIVING",  task: "Chủ đâu rồi nhỉ? — Tìm ở nhà bếp", lock: false },
    K_INIT:     { scene: "KITCHEN", task: "Kiểm tra vết máu dưới sàn", lock: false },
    K_BLOOD:    { scene: "KITCHEN", task: "Kiểm tra vết máu", lock: false },
    K_VOICE:    { scene: "KITCHEN", task: "Có tiếng gọi từ vùng tối...", lock: false },
    K_CHOICE:   { scene: "KITCHEN", task: "Nghe theo lời gọi, hay bỏ chạy?", lock: false },
    K_RUN:      { scene: "KITCHEN", task: "Chạy!", lock: true },
    K_OBEY:     { scene: "KITCHEN", task: "...", lock: true },
    H_SEARCH:   { scene: "HAUNTED", task: "Tìm người chủ... căn phòng sao lạ thế này", lock: false },
    W_WALK:     { scene: "HALLWAY", task: "Đi qua hành lang... đừng sợ", lock: false },
    W_DONE:     { scene: "HALLWAY", task: "Cửa phòng ăn đã mở!", lock: false },
    D_APPROACH: { scene: "DINING",  task: "Chủ ở đây rồi!", lock: false },
    D_JUMP:     { scene: "DINING",  task: "...", lock: true },
    D_HUG:      { scene: "DINING",  task: "...", lock: true },
    D_CAKE:     { scene: "DINING",  task: "...", lock: true },
    D_END:      { scene: "DINING",  task: "...", lock: true }
  };

  // Hội thoại / thông báo (bubble không chặn di chuyển)
  var DIALOGUES = {
    G_INIT:  { text: "Mèo ơi, vào nhà đi!", until: 3 },
    G_BUTTERFLY: { text: "Bướm kìa!", until: 2 },
    G_CHASE: { text: "Mèo bắt được bướm!", until: 2.5 },
    K_BLOOD: { text: "Vết máu dưới sàn... phải kiểm tra!", until: 2 },
    K_VOICE: { text: "Mèo ơi... lại đây...", until: 2.5 },
    H_DOOR:  { text: "Bóng tối chặn cửa! Hồn ma đẩy mèo lùi lại!", until: 2 },
    D_HUG:   { text: "Happy Birthday Yuniebel!", until: 2.5 }
  };

  var SCARE_MESSAGES = [
    "Có tiếng thì thầm...",
    "Một bóng trắng lướt qua!",
    "Đèn vụt tắt!",
    "Tiếng bước chân sau lưng...",
    "MẮT ĐỎ TRONG BÓNG TỐI!"
  ];

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
      player: { x: 420, y: 200, dir: 1, moving: false },
      darkness: 0,          // 0..1 (GARDEN tối dần / K_OBEY)
      scareCount: 0,
      fired: {},            // "phase:zone" → true (fire-once per phase)
      timers: {},           // tên → giây còn lại
      butterfly: null,      // {x, y, alive}
      knockbackCd: 0,
      choice: null,         // 1 | 2
      message: null,        // {text, until} — bubble
      scareFlash: null,     // {idx, until} — hiệu ứng hù
      chimeFlag: false,     // cutscene cảnh 6
      time: 0
    };
  }

  function startGame() {
    var s = resetGame();
    s.scene = "GARDEN";
    s.phase = "G_INIT";
    s.player = { x: SCENES.GARDEN.spawn.x, y: SCENES.GARDEN.spawn.y, dir: 1, moving: false };
    s.timers.intro = 2.0; // bubble chủ gọi
    setDialogue(s, "G_INIT");
    return s;
  }

  function setDialogue(state, key) {
    var d = DIALOGUES[key];
    if (d) state.message = { text: d.text, until: state.time + d.until };
  }

  function setPhase(state, phase, extra) {
    state.phase = phase;
    var info = PHASES[phase];
    if (info.scene === "GARDEN" || info.scene === "LIVING" || info.scene === "KITCHEN" ||
        info.scene === "HAUNTED" || info.scene === "HALLWAY" || info.scene === "DINING") {
      state.scene = info.scene;
    }
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
    // vùng tối bếp = tường vô hình trước K_CHOICE (C3-01)
    if (state.scene === "KITCHEN" && state.phase !== "K_CHOICE" && state.phase !== "K_RUN" && state.phase !== "K_OBEY") {
      if (rectsOverlap(hb, DARK_RECT)) return true;
    }
    return false;
  }

  // Di chuyển + collision slide (tách trục X/Y) + clamp biên sprite
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

  // Knockback có collision (không xuyên tường)
  function knockback(state, dx) {
    movePlayer(state, dx, 0);
    state.knockbackCd = KNOCKBACK_CD;
  }

  // ====== Trigger zones ======
  // Trả về danh sách zone fired trong frame này (theo phase active, fire-once)
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

  // ====== Bướm AI (C3-04/C2-16) ======
  function updateButterfly(state, dt) {
    var b = state.butterfly;
    if (!b || !b.alive) return;
    var sc = SCENES.GARDEN;
    var p = state.player;
    var dx = p.x - b.x, dy = p.y - b.y;
    var dist = Math.sqrt(dx * dx + dy * dy);
    var vx = Math.sin(state.time * 2) * 22;
    var vy = Math.sin(state.time * 4) * 12;
    if (state.phase === "G_CHASE" && dist < 60 && dist > 0.01) {
      vx -= (dx / dist) * BUTTERFLY_SPEED;
      vy -= (dy / dist) * BUTTERFLY_SPEED;
    }
    b.x = clamp(b.x + vx * dt, 8, sc.w - 20);
    b.y = clamp(b.y + vy * dt, 8, sc.h - 20);
  }

  function butterflyHit(state) {
    var b = state.butterfly;
    if (!b || !b.alive) return false;
    return aabb(state.player.x + HBX, state.player.y + HBY, HBW, HBH, b.x, b.y, 14, 12);
  }

  // ====== Light ======
  function hasDark(state) {
    return state.scene === "HAUNTED" || state.scene === "HALLWAY" ||
           (state.scene === "GARDEN" && state.phase === "G_DARK") ||
           (state.scene === "GARDEN" && state.phase === "G_DOOR") ||
           state.scene === "KITCHEN" && state.phase === "K_OBEY";
  }
  function inLight(state, px, py) {
    var dx = px - state.player.x, dy = py - state.player.y;
    return (dx * dx + dy * dy) <= LIGHT_RADIUS * LIGHT_RADIUS;
  }

  // ====== Main update ======
  function updateGame(state, dt, input) {
    dt = clamp(dt, 0, MAX_DT);
    state.time += dt;
    if (state.message && state.time >= state.message.until) state.message = null;
    if (state.scareFlash && state.time >= state.scareFlash.until) state.scareFlash = null;
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
    }

    var phinfo = PHASES[state.phase];
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
      } else if (!locked) {
        state.player.moving = false;
      }
    }

    var zones = checkZones(state);
    var sc = SCENES[state.scene];
    var i, z;

    switch (state.phase) {
      case "TITLE":
        break;

      case "G_INIT":
        if (state.timers.intro <= 0) state.message = null;
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door") {
            setPhase(state, "G_BUTTERFLY");
            state.butterfly = { x: SCENES.GARDEN.butterfly.x, y: SCENES.GARDEN.butterfly.y, alive: true };
            state.timers.bfly = 1.5; // hover trước khi tránh
            setDialogue(state, "G_BUTTERFLY");
          }
        }
        break;

      case "G_BUTTERFLY":
        updateButterfly(state, dt);
        if (butterflyHit(state)) {
          state.butterfly = null;
          setPhase(state, "G_DARK");
          state.darkness = 0;
          state.timers.dark = 5.0;
          setDialogue(state, "G_CHASE");
          return;
        }
        if (state.timers.bfly <= 0) setPhase(state, "G_CHASE");
        break;

      case "G_CHASE":
        updateButterfly(state, dt);
        if (butterflyHit(state)) {
          state.butterfly = null;
          setPhase(state, "G_DARK");
          state.darkness = 0;
          state.timers.dark = 5.0;
          setDialogue(state, "G_CHASE");
          return;
        }
        break;

      case "G_DARK":
        state.darkness = clamp(1 - state.timers.dark / 5.0, 0, 1);
        if (state.darkness >= 1) setPhase(state, "G_DOOR");
        break;

      case "G_DOOR":
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door") {
            setPhase(state, "L_SEARCH");
            state.player.x = SCENES.LIVING.spawn.x;
            state.player.y = SCENES.LIVING.spawn.y;
            return;
          }
        }
        break;

      case "L_SEARCH":
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door_kitchen") {
            setPhase(state, "K_INIT");
            state.player.x = SCENES.KITCHEN.spawn.x;
            state.player.y = SCENES.KITCHEN.spawn.y;
            return;
          }
        }
        break;

      case "K_INIT":
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "blood") {
            setPhase(state, "K_BLOOD");
            state.timers.blood = 1.5;
            setDialogue(state, "K_BLOOD");
            return;
          }
        }
        break;

      case "K_BLOOD":
        if (state.timers.blood <= 0) {
          setPhase(state, "K_VOICE");
          state.timers.voice = 2.0;
          setDialogue(state, "K_VOICE");
        }
        break;

      case "K_VOICE":
        if (state.timers.voice <= 0) setPhase(state, "K_CHOICE");
        break;

      case "K_CHOICE":
        if (input.choice1 === 1 || input.choice2 === 1) {
          state.choice = 1;
          setPhase(state, "K_RUN");
          state.timers.run = 1.8;
          return;
        }
        if (input.choice1 === 2 || input.choice2 === 2) {
          state.choice = 2;
          setPhase(state, "K_OBEY");
          state.timers.obey = 2.5;
          return;
        }
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "dark") {
            state.choice = 2;
            setPhase(state, "K_OBEY");
            state.timers.obey = 2.5;
            return;
          }
        }
        break;

      case "K_RUN":
        // mèo tự chạy về phòng khách
        movePlayer(state, -WALK_SPEED * dt, 0);
        if (state.player.x <= 40 || state.timers.run <= 0) {
          setPhase(state, "H_SEARCH");
          state.player.x = SCENES.HAUNTED.spawn.x;
          state.player.y = SCENES.HAUNTED.spawn.y;
          state.darkness = 0;
        }
        break;

      case "K_OBEY":
        // mèo tự đi vào bóng tối (góc trên trái)
        movePlayer(state, -WALK_SPEED * 0.6 * dt, -WALK_SPEED * 0.15 * dt);
        state.darkness = clamp(1 - state.timers.obey / 2.5, 0, 1);
        if (state.darkness >= 1) {
          state.scene = "GAMEOVER";
          state.phase = "GAMEOVER";
          state.gameOver = true;
          return;
        }
        break;

      case "H_SEARCH":
        for (i = 0; i < zones.length; i++) {
          z = zones[i];
          if (z.id === "door_front") {
            if (state.knockbackCd <= 0) {
              knockback(state, -KNOCKBACK);
              setDialogue(state, "H_DOOR");
              state.scareFlash = { idx: 0, until: state.time + 0.4 };
            }
            // cho phép fire lại khi quay lại cửa (đẩy lùi MỖI lần cố đi ra)
            delete state.fired[zoneKey(state.phase, z.id)];
          } else if (z.id === "door_hall") {
            setPhase(state, "W_WALK");
            state.scareCount = 0;
            state.player.x = SCENES.HALLWAY.spawn.x;
            state.player.y = SCENES.HALLWAY.spawn.y;
            return;
          }
        }
        break;

      case "W_WALK":
        for (i = 0; i < zones.length; i++) {
          z = zones[i];
          if (z.id.indexOf("scare") === 0) {
            state.scareCount++;
            var idx = Math.min(state.scareCount, 5) - 1;
            state.scareFlash = { idx: idx, until: state.time + 0.5 };
            state.message = { text: SCARE_MESSAGES[idx % SCARE_MESSAGES.length], until: state.time + 1.6 };
            if (state.scareCount >= 5) {
              setPhase(state, "W_DONE");
              return;
            }
          }
        }
        break;

      case "W_DONE":
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "door_dining") {
            setPhase(state, "D_APPROACH");
            state.player.x = SCENES.DINING.spawn.x;
            state.player.y = SCENES.DINING.spawn.y;
            return;
          }
        }
        break;

      case "D_APPROACH":
        for (i = 0; i < zones.length; i++) {
          if (zones[i].id === "approach") {
            setPhase(state, "D_JUMP");
            state.timers.jump = 1.2;
            return;
          }
        }
        break;

      case "D_JUMP":
        // mèo tự tiến tới bàn rồi nhảy lên
        movePlayer(state, 0, 0); // giữ yên; nhảy mô tả bằng hiệu ứng ở game.js
        if (state.timers.jump <= 0) {
          setPhase(state, "D_HUG");
          state.timers.hug = 1.8;
          setDialogue(state, "D_HUG");
          state.chimeFlag = true;
        }
        break;

      case "D_HUG":
        if (state.timers.hug <= 0) {
          setPhase(state, "D_CAKE");
          state.timers.cake = 2.6;
        }
        break;

      case "D_CAKE":
        if (state.timers.cake <= 0) {
          state.scene = "END";
          state.phase = "END";
        }
        break;

      default:
        break;
    }
  }

  // ====== Export (test) ======
  return {
    resetGame: resetGame,
    startGame: startGame,
    updateGame: updateGame,
    movePlayer: movePlayer,
    collides: collides,
    checkZones: checkZones,
    updateButterfly: updateButterfly,
    hasDark: hasDark,
    inLight: inLight,
    setPhase: setPhase,
    PHASES: PHASES,
    SCENES: SCENES,
    LIGHT_RADIUS: LIGHT_RADIUS,
    WALK_SPEED: WALK_SPEED,
    MAX_DT: MAX_DT
  };
});
