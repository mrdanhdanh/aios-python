/* GameScene.js — Yuniebel's Cat (TASK-081, bản Phaser 4)
 * 1 SCENE DUY NHẤT (P3-1): re-render bg texture mỗi frame theo state.core (P1-1);
 * sprite động Player+Butterfly (P1-B2); camera scroll; overlay; audio + UI sync.
 * Port render/loop từ game.js vanilla — KHÔNG đổi hành vi game (core byte-identical).
 */
import Phaser from "phaser";
import { camX, handleSoundFlags, makeSyncUI } from "../ui/ui.js";

// depth ordering (R7): bg 0 < sprite 10 < "!" 20 < flash/fade 30
const D_BG = 0, D_SPRITE = 10, D_MARK = 20, D_OVERLAY = 30;

export default class GameScene extends Phaser.Scene {
  constructor() {
    super({ key: "Game" });
  }

  create() {
    this.S = window.Sprites;
    this.gameCore = window.__coreGame;
    this.state = this.gameCore.state;
    this.audio = window.__audioFX;
    this.syncUI = makeSyncUI(this.gameCore, this.audio);

    this.prevScene = "TITLE";
    this.fadeT = 0;
    this.footstepTimer = 0;
    this._frozenTime = null; // R1: đóng băng render time khi s.frozen (determinism)

    // ===== 9 bg CanvasTexture (create-once — P2-B1); GARDEN/HALLWAY 320 logical = 960×270 =====
    const bgDefs = {
      title: [480, 270], garden: [960, 270], living: [480, 270], kitchen: [480, 270],
      haunted: [480, 270], hallway: [960, 270], birthday: [480, 270],
      gameover: [480, 270], end: [480, 270]
    };
    this.bgTex = {};
    for (const k in bgDefs) {
      const key = "bg-" + k;
      if (!this.textures.exists(key)) this.textures.createCanvas(key, bgDefs[k][0], bgDefs[k][1]);
      this.bgTex[k] = this.textures.get(key);
    }
    this.bgImg = this.add.image(0, 0, "bg-title").setOrigin(0, 0).setDepth(D_BG);

    // ===== Player sprite: 144×96 (48 logical ngang — P1-B1), anchor (0,0), KHÔNG setFlipX =====
    if (!this.textures.exists("spr-cat")) this.textures.createCanvas("spr-cat", 144, 96);
    this.catTex = this.textures.get("spr-cat");
    this.catImg = this.add.image(0, 0, "spr-cat").setOrigin(0, 0).setDepth(D_SPRITE).setVisible(false);

    // ===== Butterfly sprite: 96×96 (32 logical), anchor (0.5, 0.5) =====
    if (!this.textures.exists("spr-butterfly")) this.textures.createCanvas("spr-butterfly", 96, 96);
    this.bfTex = this.textures.get("spr-butterfly");
    this.bfImg = this.add.image(0, 0, "spr-butterfly").setOrigin(0.5, 0.5).setDepth(D_SPRITE).setVisible(false);

    // ===== "!" marks trên đầu mèo (P2-B2: 30px/42px = (10|14)*GX) =====
    this.markText = this.add.text(0, 0, "", {
      fontFamily: "monospace", fontSize: "30px", color: "#ffffff", fontStyle: "bold"
    }).setDepth(D_MARK).setVisible(false);

    // ===== Overlay screen-space (setScrollFactor(0) — không bị camera dịch) =====
    this.flashRect = this.add.rectangle(0, 0, 480, 270, 0xffffff, 0).setOrigin(0, 0).setDepth(D_OVERLAY).setScrollFactor(0);
    this.fadeRect = this.add.rectangle(0, 0, 480, 270, 0x000000, 0).setOrigin(0, 0).setDepth(D_OVERLAY).setScrollFactor(0);
  }

  update(time, delta) {
    const s = this.state;
    const dt = Math.min(delta / 1000, 0.05); // P3-B7: Phaser delta ms → core dt giây

    // ===== input map (window listeners đặt trong main.js — P3-3) =====
    const input = {
      up: window.__keys["w"] || window.__keys["arrowup"] || window.__dpad.up,
      down: window.__keys["s"] || window.__keys["arrowdown"] || window.__dpad.down,
      left: window.__keys["a"] || window.__keys["arrowleft"] || window.__dpad.left,
      right: window.__keys["d"] || window.__keys["arrowright"] || window.__dpad.right,
      start: window.__oneShot.start,
      choice1: window.__oneShot.choice1,
      choice2: window.__oneShot.choice2
    };
    window.__oneShot.start = false;
    window.__oneShot.choice1 = false;
    window.__oneShot.choice2 = false;

    const prevScene = s.scene;
    this.gameCore.update(dt, input);

    // fade chuyển cảnh (P3-2) — đứng yên khi frozen (visual determinism)
    if (s.scene !== prevScene) this.fadeT = 0.35;
    if (this.fadeT > 0 && !s.frozen) this.fadeT -= dt;

    // ===== camera scroll (GARDEN/HALLWAY 320 logical → 960px) =====
    this.cameras.main.setScroll(camX(s) * 3, 0);

    // ===== render =====
    // R1: khi s.frozen, đóng băng render time (capture lần đầu) để bg/sprite deterministic
    // (core đã freeze s.time khi frozen → sprite dùng s.time cũng deterministic; riêng drawGarden/drawKitchen...
    //  nhận param `time` từ Phaser loop nên phải freeze thủ công ở đây — AC-13 / visual spec)
    const rtime = s.frozen ? (this._frozenTime ?? (this._frozenTime = time)) : (this._frozenTime = null, time);
    this.renderBg(rtime);
    this.renderSprites(time);
    this.renderOverlays();

    // ===== audio (port vanilla) =====
    handleSoundFlags(s, this.audio);
    if (s.player.moving) {
      this.footstepTimer += dt;
      if (this.footstepTimer > 0.28) {
        this.footstepTimer = 0;
        if (s.scene === "HALLWAY") this.audio.footstepEcho(); else this.audio.footstepGrass();
      }
    }
    if (s.scene === "GARDEN" && Math.floor(s.time * 1.7) % 30 === 0) this.audio.bird();
    if (s.scene === "LIVING" && Math.floor(s.time * 2) % 45 === 0) this.audio.clockTick();

    // ===== DOM overlay =====
    this.syncUI();
  }

  // ===== Nền: vẽ lại mỗi frame vào CanvasTexture rồi refresh (P1-1/P1-B3) =====
  renderBg(time) {
    const s = this.state;
    const key = (s.scene || "TITLE").toLowerCase();
    const tex = this.bgTex[key];
    if (!tex) return;
    if (this.prevScene !== s.scene) {
      this.bgImg.setTexture("bg-" + key);
      this.prevScene = s.scene;
    }
    const ctx = tex.getContext();
    ctx.clearRect(0, 0, tex.width, tex.height);
    switch (s.scene) {
      case "TITLE":
        this.S.drawTitle(ctx, time);
        break;
      case "GARDEN":
        this.S.drawGarden(ctx, s, time, 0); // cx=0 — vẽ toàn bộ map 320 logical
        // overlay đêm world-space (P1-B3 — port game.js vanilla)
        if (s.darkness > 0.5) {
          ctx.fillStyle = "rgba(8,10,30," + (s.darkness - 0.5) * 0.6 + ")";
          ctx.fillRect(0, 0, tex.width, tex.height);
          ctx.fillStyle = "rgba(255,217,59,0.12)";
          ctx.fillRect(287 * 3 - 12, 38 * 3, 24, 30); // đèn hiên (287,38) logical
        }
        break;
      case "LIVING":
        this.S.drawLiving(ctx, time);
        break;
      case "KITCHEN":
        this.S.drawKitchen(ctx, s, time);
        break;
      case "HAUNTED":
        this.S.drawHaunted(ctx, s, time); // ghost đã xử lý ẩn/hiện trong sprites.js (P1-B2)
        break;
      case "HALLWAY":
        this.S.drawHallway(ctx, s, time, 0); // 5 scare world 130..300 nằm trong bg (P1-B2)
        break;
      case "BIRTHDAY":
        this.S.drawBirthday(ctx, s, time);
        break;
      case "GAMEOVER":
        this.S.drawGameOver(ctx);
        break;
      case "END":
        this.S.drawEnd(ctx, time);
        break;
    }
    tex.refresh();
  }

  // ===== Sprite động: Player + Butterfly duy nhất (P1-B2) =====
  renderSprites(time) {
    const s = this.state;
    const p = s.player;
    const inGameplay = ["GARDEN", "LIVING", "KITCHEN", "HAUNTED", "HALLWAY", "BIRTHDAY"].indexOf(s.scene) !== -1;

    // player — vẽ drawCat(ctx, 14, 8, ...) vào texture 144×96; position bù offset (R2)
    if (inGameplay) {
      const ctx = this.catTex.getContext();
      ctx.clearRect(0, 0, 144, 96);
      let fr = 0;
      if (p.moving) fr = Math.floor(s.time * 8) % 2;
      this.S.drawCat(ctx, 14, 8, p.dir, fr, s.time);
      this.catTex.refresh();
      this.catImg.setPosition(p.x * 3 - 42, p.y * 3 - 24); // R2: bù 14 logical ngang + 8 dọc
      this.catImg.setVisible(true);
    } else {
      this.catImg.setVisible(false);
    }

    // butterfly (chỉ GARDEN — vanilla vẽ riêng ngoài drawGarden)
    if (s.scene === "GARDEN" && s.butterfly) {
      const b = s.butterfly;
      const bctx = this.bfTex.getContext();
      bctx.clearRect(0, 0, 96, 96);
      this.S.drawButterfly(bctx, 16, 16, s.time); // padding 16 — bướm 8×6 quanh tâm
      this.bfTex.refresh();
      this.bfImg.setPosition(b.x * 3, b.y * 3);
      this.bfImg.setVisible(true);
    } else {
      this.bfImg.setVisible(false);
    }

    // "!" marks (P2-B2: 30px/42px; world = screen + camX*3)
    if (s.scareActive) {
      const marks = ["!", "!!", "!!!", "!?", "!!!", "!!!"];
      this.markText.setText(marks[s.scareActive - 1]);
      this.markText.setFontSize(s.scareActive === 5 ? "42px" : "30px");
      this.markText.setPosition(p.x * 3 + 4, p.y * 3 - 4);
      this.markText.setVisible(true);
    } else {
      this.markText.setVisible(false);
    }
  }

  renderOverlays() {
    const s = this.state;
    // flash jump scare (vanilla: rgba(255,255,255, flash*0.7))
    this.flashRect.setAlpha(s.flash * 0.7);
    // fade chuyển cảnh (vanilla: (fadeT/0.35)*0.6)
    this.fadeRect.setAlpha(this.fadeT > 0 ? (this.fadeT / 0.35) * 0.6 : 0);
  }
}
