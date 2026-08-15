/* game.js — Yuniebel's Cat (TASK-078) — game loop + render + input + UI + debug hook
 * Browser only. MỌI animation dùng state.time (R1). Debug hook active khi ?test=1.
 */
(function () {
  "use strict";
  var core = window.AiosCore;
  var S = window.Sprites;
  var audio = window.AudioFX();
  var CW = 480, CH = 270;
  var canvas = document.getElementById("game");
  var ctx = canvas.getContext("2d");
  canvas.width = CW; canvas.height = CH;

  function resize() {
    var w = window.innerWidth, h = window.innerHeight;
    var s = Math.min(w / CW, h / CH);
    canvas.style.width = Math.floor(CW * s) + "px";
    canvas.style.height = Math.floor(CH * s) + "px";
  }
  window.addEventListener("resize", resize); resize();

  // ===== Game instance =====
  var game = core.createGame();
  var state = game.state;
  var fadeT = 0, fadeDir = 0;      // 0 idle, 1 out, -1 in
  var footstepTimer = 0;

  var debugEnabled = /[?&]test=1/.test(window.location.search);

  // ===== INPUT =====
  var keys = {}, dpad = { up: false, down: false, left: false, right: false };
  var isTouch = ("ontouchstart" in window) || navigator.maxTouchPoints > 0;
  var oneShot = { start: false, choice1: false, choice2: false };

  function kN(e) { return e.key.toLowerCase(); }
  window.addEventListener("keydown", function (e) {
    var k = kN(e);
    if (["w", "a", "s", "d", "arrowup", "arrowdown", "arrowleft", "arrowright", " "].indexOf(k) !== -1) e.preventDefault();
    if (e.repeat) return;
    audio.init(); // C2-15: gesture đầu resume
    keys[k] = true;
    if (k === "1" && state.phase === "K_CHOICE") oneShot.choice1 = true;
    if (k === "2" && state.phase === "K_CHOICE") oneShot.choice2 = true;
    if ((k === "enter" || k === " ") && (state.scene === "TITLE" || state.scene === "GAMEOVER" || state.scene === "END")) oneShot.start = true;
  });
  window.addEventListener("keyup", function (e) { keys[kN(e)] = false; });
  window.addEventListener("blur", clearKeys);
  document.addEventListener("visibilitychange", function () { if (document.hidden) clearKeys(); else audio.init(); });
  function clearKeys() { for (var k in keys) keys[k] = false; }

  function bPad(id, dir) {
    var el = document.getElementById(id); if (!el) return;
    el.addEventListener("touchstart", function (e) { e.preventDefault(); dpad[dir] = true; audio.init(); });
    el.addEventListener("touchend", function (e) { e.preventDefault(); dpad[dir] = false; });
    el.addEventListener("touchcancel", function () { dpad[dir] = false; });
  }
  bPad("pad-up", "up"); bPad("pad-down", "down"); bPad("pad-left", "left"); bPad("pad-right", "right");
  if (isTouch) { document.getElementById("dpad").classList.remove("hidden"); document.getElementById("hint").classList.add("hidden"); }

  // ===== UI elements =====
  var uiTask = document.getElementById("task-box"), taskText = document.getElementById("task-text");
  var uiBtn = document.getElementById("ui-toggle");
  var diagEl = document.getElementById("dialogue"), diagText = document.getElementById("dialogue-text");
  var choiceEl = document.getElementById("choice-box");
  var scareC = document.getElementById("scare-counter");
  var titleEl = document.getElementById("title-screen"), overEl = document.getElementById("gameover-screen"), endEl = document.getElementById("end-screen");
  var hintEl = document.getElementById("hint");
  var muteBtn = document.getElementById("mute-btn");
  var uiHidden = false;

  uiBtn.addEventListener("click", function () { uiHidden = !uiHidden; uiTask.classList.toggle("hidden", uiHidden); hintEl.classList.toggle("hidden", uiHidden); });
  document.getElementById("task-close").addEventListener("click", function () { game.reset(); fadeT = 0; syncUI(); });
  document.getElementById("btn-start").addEventListener("click", function () { oneShot.start = true; audio.init(); });
  document.getElementById("btn-replay-1").addEventListener("click", function () { oneShot.start = true; audio.init(); });
  document.getElementById("btn-replay-2").addEventListener("click", function () { oneShot.start = true; audio.init(); });
  document.getElementById("choice-1").addEventListener("click", function () { oneShot.choice1 = true; audio.init(); });
  document.getElementById("choice-2").addEventListener("click", function () { oneShot.choice2 = true; audio.init(); });
  muteBtn.addEventListener("click", function () { audio.setMuted(!audio.isMuted()); muteBtn.textContent = audio.isMuted() ? "🔇" : "🔊"; });

  function syncUI() {
    var inTitle = state.scene === "TITLE", inOver = state.scene === "GAMEOVER", inEnd = state.scene === "END";
    titleEl.classList.toggle("hidden", !inTitle);
    overEl.classList.toggle("hidden", !inOver);
    endEl.classList.toggle("hidden", !inEnd);
    uiTask.classList.toggle("hidden", uiHidden || inTitle || inOver || inEnd);
    if (!inTitle && !inOver && !inEnd) {
      var info = core.PHASES[state.phase];
      taskText.textContent = info ? info.task : "";
    }
    // hộp lựa chọn (K_CHOICE)
    choiceEl.classList.toggle("hidden", state.phase !== "K_CHOICE");
    // scare counter (hành lang)
    if (state.scene === "HALLWAY") {
      scareC.classList.remove("hidden");
      scareC.textContent = "👻 " + state.scareCount + "/5";
    } else {
      scareC.classList.add("hidden");
    }
    // hội thoại
    if (state.dialogue) {
      diagEl.classList.remove("hidden");
      diagText.textContent = state.dialogue.text;
      diagEl.classList.toggle("thought", !!state.dialogue.thought);
    } else {
      diagEl.classList.add("hidden");
    }
  }

  // ===== CAMERA (logical viewport 160 — R2: thay toàn bộ, bỏ guard sc.w <= CW cũ) =====
  function camX() {
    var sc = core.SCENES[state.scene];
    if (!sc) return 0; // TITLE/END không có scene map
    return Math.max(0, Math.min(state.player.x - 80 + 3, sc.w - 160));
  }

  // ===== SOUND FLAGS (game.js phát 1 lần rồi xóa) =====
  function handleSoundFlags() {
    var f = state.soundFlags;
    for (var k in f) {
      if (!f[k]) continue;
      switch (k) {
        case "ting": audio.ting(); break;
        case "flutter": audio.flutter(); break;
        case "meow": audio.meow(); break;
        case "happyMeow": audio.happyMeow(); break;
        case "scaredMeow": audio.scaredMeow(); break;
        case "painMeow": audio.painMeow(); break;
        case "footstepGrass": audio.footstepGrass(); break;
        case "footstepEcho": audio.footstepEcho(); break;
        case "wind": audio.wind(); break;
        case "bird": audio.bird(); break;
        case "clockTick": audio.clockTick(); break;
        case "drip": audio.drip(); break;
        case "whisper": audio.whisper(); break;
        case "whisperFar": audio.whisperFar(); break;
        case "rush": audio.rush(); break;
        case "swoosh": audio.swoosh(); break;
        case "whoosh": audio.whoosh(); break;
        case "creak": audio.creak(); break;
        case "jumpscare": audio.jumpscare(); break;
        case "candle": audio.candle(); break;
        case "bell": audio.bell(); break;
        case "sparkle": audio.sparkle(); break;
        case "uiClick": audio.uiClick(); break;
        case "intro": audio.bird(); audio.wind(); break;
        case "darkStart": audio.ting(); break;
        case "start": audio.resetStats(); break; // C2-16/R-02
      }
      delete f[k];
    }
    // mood theo phase (§6.3)
    var expectedMood = moodForPhase(state);
    if (expectedMood && audio.getMood() !== expectedMood) audio.setMood(expectedMood);
  }

  function moodForPhase(s) {
    switch (s.phase) {
      case "TITLE": return "calm-happy";
      case "G_INIT": case "G_CHASE": return "garden-calm";
      case "G_DARK": case "G_DOOR": return "dusk-sad";
      case "L_SEARCH": return "mystery";
      case "K_INIT": case "K_BLOOD": case "K_CHOICE": return "kitchen-mystery";
      case "H_INIT": case "H_BLOCK": case "H_EXIT": return "tense";
      case "W_INIT": case "W_WALK": return "suspense";
      case "W_DONE": return "warm";
      case "D_END": return "celebration";
      case "GAME_OVER": return "dusk-sad";
      case "END": return "celebration";
      default: return null;
    }
  }

  // ===== RENDER =====
  function drawScene(cx) {
    var sc = core.SCENES[state.scene];
    switch (state.scene) {
      case "TITLE":
        S.drawTitle(ctx, state.time);
        break;
      case "GARDEN":
        S.drawGarden(ctx, state, state.time, cx);
        // bướm
        if (state.butterfly && state.butterflyVisible !== false) {
          S.drawButterfly(ctx, state.butterfly.x - cx, state.butterfly.y, state.time);
        }
        // dark overlay (trời tối thêm)
        if (state.darkness > 0.5) {
          ctx.fillStyle = "rgba(8,10,30," + (state.darkness - 0.5) * 0.6 + ")";
          ctx.fillRect(0, 0, CW, CH);
        }
        // đèn hiên sáng (đêm) — khớp sprite đèn (287,38) trong drawGarden
        if (state.darkness > 0.5) {
          var lx = (287 - cx) * S.GX;
          ctx.fillStyle = "rgba(255,217,59,0.12)";
          ctx.fillRect(lx - 12, 38 * S.GX, 24, 30);
        }
        break;
      case "LIVING":
        S.drawLiving(ctx, state.time);
        break;
      case "KITCHEN":
        S.drawKitchen(ctx, state, state.time);
        break;
      case "HAUNTED":
        S.drawHaunted(ctx, state, state.time);
        break;
      case "HALLWAY":
        S.drawHallway(ctx, state, state.time, cx);
        break;
      case "BIRTHDAY":
        S.drawBirthday(ctx, state, state.time);
        break;
      case "GAMEOVER":
        S.drawGameOver(ctx);
        break;
      case "END":
        S.drawEnd(ctx, state.time);
        break;
    }
    // dấu hù trên đầu mèo (!/!!/!!!/!?)
    if (state.scareActive) {
      var marks = ["!", "!!", "!!!", "!?", "!!!", "!!!"];
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold " + (state.scareActive === 5 ? 14 : 10) * S.GX + "px monospace";
      ctx.fillText(marks[state.scareActive - 1], (state.player.x - cx) * S.GX + 4, state.player.y * S.GX - 4);
    }
    // flash jump scare
    if (state.flash > 0) {
      ctx.fillStyle = "rgba(255,255,255," + state.flash * 0.7 + ")";
      ctx.fillRect(0, 0, CW, CH);
    }
  }

  function drawPlayer(cx) {
    var p = state.player;
    var fr = 0;
    if (p.moving) fr = Math.floor(state.time * 8) % 2;
    S.drawCat(ctx, p.x - cx, p.y, p.dir, fr, state.time);
  }

  // ===== UPDATE =====
  function update(dt) {
    // input map
    var input = {
      up: keys["w"] || keys["arrowup"] || dpad.up,
      down: keys["s"] || keys["arrowdown"] || dpad.down,
      left: keys["a"] || keys["arrowleft"] || dpad.left,
      right: keys["d"] || keys["arrowright"] || dpad.right,
      start: oneShot.start,
      choice1: oneShot.choice1,
      choice2: oneShot.choice2
    };
    oneShot.start = false; oneShot.choice1 = false; oneShot.choice2 = false;

    var prevScene = state.scene;
    game.update(dt, input);

    // fade chuyển cảnh — R1: khi frozen (chụp ảnh) fade dừng lại để ảnh ổn định
    if (state.scene !== prevScene) { fadeT = 0.35; }
    if (fadeT > 0 && !state.frozen) fadeT -= dt;

    handleSoundFlags();

    // bước chân
    if (state.player.moving) {
      footstepTimer += dt;
      if (footstepTimer > 0.28) {
        footstepTimer = 0;
        if (state.scene === "HALLWAY") audio.footstepEcho(); else audio.footstepGrass();
      }
    }

    // ambient theo scene
    if (state.scene === "GARDEN" && Math.floor(state.time * 1.7) % 30 === 0) audio.bird();
    if (state.scene === "LIVING" && Math.floor(state.time * 2) % 45 === 0) audio.clockTick();

    syncUI();
  }

  // ===== LOOP =====
  var last = performance.now();
  function loop(now) {
    var dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    update(dt);
    var cx = camX();
    ctx.clearRect(0, 0, CW, CH);
    drawScene(cx);
    drawPlayer(cx);
    if (fadeT > 0) {
      ctx.fillStyle = "rgba(0,0,0," + (fadeT / 0.35) * 0.6 + ")";
      ctx.fillRect(0, 0, CW, CH);
    }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  // ===== DEBUG HOOK (chỉ khi ?test=1 — C1-15) =====
  if (debugEnabled) {
    window.__yuniebel = {
      debug: game.debug,
      getState: function () { return state; },
      audio: audio,
      core: core
    };
  }
})();
