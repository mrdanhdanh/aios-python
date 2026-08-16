/* ui.js — Yuniebel's Cat (TASK-081, bản Phaser) — port từ game.js vanilla
 * DOM overlay sync (task/dialogue/choice/scare/title/gameover/end) + camX + audio bridge.
 * KHÔNG đụng render — GameScene lo render Phaser.
 */

// ===== CAMERA (logical viewport 160 — port nguyên văn game.js vanilla) =====
export function camX(state) {
  var sc = window.AiosCore.SCENES[state.scene];
  if (!sc) return 0; // TITLE/END không có scene map
  return Math.max(0, Math.min(state.player.x - 80 + 3, sc.w - 160));
}

// ===== Mood theo phase (§6.3 — port nguyên văn) =====
export function moodForPhase(s) {
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

// ===== SOUND FLAGS (port nguyên văn game.js vanilla — phát 1 lần rồi xóa) =====
export function handleSoundFlags(state, audio) {
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

// ===== UI elements + sync (port nguyên văn game.js vanilla) =====
var uiHidden = false;

export function createUI(game, audio) {
  var state = game.state;
  var uiTask = document.getElementById("task-box"), taskText = document.getElementById("task-text");
  var uiBtn = document.getElementById("ui-toggle");
  var diagEl = document.getElementById("dialogue"), diagText = document.getElementById("dialogue-text");
  var choiceEl = document.getElementById("choice-box");
  var scareC = document.getElementById("scare-counter");
  var titleEl = document.getElementById("title-screen"), overEl = document.getElementById("gameover-screen"), endEl = document.getElementById("end-screen");
  var hintEl = document.getElementById("hint");
  var muteBtn = document.getElementById("mute-btn");

  uiBtn.addEventListener("click", function () { uiHidden = !uiHidden; uiTask.classList.toggle("hidden", uiHidden); hintEl.classList.toggle("hidden", uiHidden); });
  document.getElementById("task-close").addEventListener("click", function () { game.reset(); syncUI(); });
  document.getElementById("btn-start").addEventListener("click", function () { window.__oneShot.start = true; audio.init(); });
  document.getElementById("btn-replay-1").addEventListener("click", function () { window.__oneShot.start = true; audio.init(); });
  document.getElementById("btn-replay-2").addEventListener("click", function () { window.__oneShot.start = true; audio.init(); });
  document.getElementById("choice-1").addEventListener("click", function () { window.__oneShot.choice1 = true; audio.init(); });
  document.getElementById("choice-2").addEventListener("click", function () { window.__oneShot.choice2 = true; audio.init(); });
  muteBtn.addEventListener("click", function () { audio.setMuted(!audio.isMuted()); muteBtn.textContent = audio.isMuted() ? "🔇" : "🔊"; });

  function syncUI() {
    var inTitle = state.scene === "TITLE", inOver = state.scene === "GAMEOVER", inEnd = state.scene === "END";
    titleEl.classList.toggle("hidden", !inTitle);
    overEl.classList.toggle("hidden", !inOver);
    endEl.classList.toggle("hidden", !inEnd);
    uiTask.classList.toggle("hidden", uiHidden || inTitle || inOver || inEnd);
    if (!inTitle && !inOver && !inEnd) {
      var info = window.AiosCore.PHASES[state.phase];
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

  return { syncUI: syncUI };
}

// Re-export syncUI với closure đơn giản (GameScene gọi mỗi frame)
export function makeSyncUI(game, audio) {
  var ui = createUI(game, audio);
  return ui.syncUI;
}
