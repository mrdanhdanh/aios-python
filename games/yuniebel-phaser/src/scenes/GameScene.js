/* GameScene.js — Yuniebel's Cat (TASK-082, bản Phaser 4 — nâng cấp hướng E)
 * A: sprite sheet PNG thật + Phaser Animation (mèo walk 4f/idle-cycle, bướm vỗ cánh,
 *    ma float, chủ, bánh kem nến cháy) — thay drawCat/drawButterfly canvas primitives.
 * B: fx deterministic seeded (bụi, đom đóm, hơi thở ma, tia lửa) + light pool thay overlay đêm.
 * C: parallax (farTex mây / nearTex cỏ) + camera shake khi scare + zoom nhẹ scare 5.
 * D: fade ease-out + night tint lerp.
 * Ràng buộc: vendor core/sprites/audio byte-identical; determinism frozen (rtime + anims pause).
 */
import Phaser from "phaser";
import { camX, handleSoundFlags, makeSyncUI } from "../ui/ui.js";
import { renderFx, renderLightPool, nightTintAlpha, fadeAlpha } from "../fx/fx.js";
// Vite import module → emit vào dist (C1-04)
import catUrl from "../assets/cat.png";
import butterflyUrl from "../assets/butterfly.png";
import ghostUrl from "../assets/ghost.png";
import ownerUrl from "../assets/owner.png";
import cakeUrl from "../assets/cake.png";

// depth ordering: bg 0 < far 0.05 < near 0.08 < sprite 10 < mark 20 < fx 25 < tint 26 < pool 27 < flash/fade 30 (C2-08)
const D_BG = 0, D_FAR = 0.05, D_NEAR = 0.08, D_SPRITE = 10, D_MARK = 20, D_FX = 25, D_TINT = 26, D_POOL = 27, D_OVERLAY = 30;

export default class GameScene extends Phaser.Scene {
  constructor() {
    super({ key: "Game" });
  }

  preload() {
    // C1-05: load.spritesheet (Phaser 4.2.1 FileTypesManager) — cake 2 frames 60×48 (C2v2-16)
    this.load.spritesheet("cat", catUrl, { frameWidth: 48, frameHeight: 48 });
    this.load.spritesheet("butterfly", butterflyUrl, { frameWidth: 48, frameHeight: 48 });
    this.load.spritesheet("ghost", ghostUrl, { frameWidth: 54, frameHeight: 72 });
    this.load.spritesheet("cake", cakeUrl, { frameWidth: 60, frameHeight: 48 });
    this.load.image("owner", ownerUrl);
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
    this._prevScare = 0;     // R-07.2: khởi tạo 0 — tránh shake nhầm frame đầu
    this._frozen = false;    // C2v2-17: trạng thái pauseAll anims
    this._zoom = 1;          // C: zoom hiện tại (manual lerp — không dùng zoomTo Phaser)

    // ===== Animations (A) =====
    this.anims.create({ key: "cat-walk", frames: [
      { key: "cat", frame: 0 }, { key: "cat", frame: 1 }, { key: "cat", frame: 2 }, { key: "cat", frame: 3 }
    ], frameRate: 8, repeat: -1 });
    // idle-cycle 1 anim duy nhất (C2-04): idle(4) → blink(5) → idle(4) → idle(4) → tail0(6) → tail1(7)
    this.anims.create({ key: "cat-idle-cycle", frames: [
      { key: "cat", frame: 4 }, { key: "cat", frame: 5 }, { key: "cat", frame: 4 }, { key: "cat", frame: 4 },
      { key: "cat", frame: 6 }, { key: "cat", frame: 7 }
    ], frameRate: 4, repeat: -1 });
    this.anims.create({ key: "bfl-flutter", frames: [
      { key: "butterfly", frame: 0 }, { key: "butterfly", frame: 1 }, { key: "butterfly", frame: 2 }, { key: "butterfly", frame: 3 }
    ], frameRate: 12, repeat: -1 });
    this.anims.create({ key: "ghost-float", frames: [
      { key: "ghost", frame: 0 }, { key: "ghost", frame: 1 }
    ], frameRate: 3, repeat: -1 });
    this.anims.create({ key: "cake-flame", frames: [
      { key: "cake", frame: 0 }, { key: "cake", frame: 1 }
    ], frameRate: 5, repeat: -1 });

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

    // ===== Player sprite sheet (A): frame 48×48, mèo 16×16 logical chiếm trọn (C1-02) =====
    // add.sprite (KHÔNG image) — cần AnimationState cho anims.play (AC-3 debug)
    this.catImg = this.add.sprite(0, 0, "cat").setOrigin(0.5, 0.5).setDepth(D_SPRITE).setVisible(false);

    // ===== Butterfly sprite sheet (A): 8×6 logical ở tâm frame (C2v2-06) =====
    this.bfImg = this.add.sprite(0, 0, "butterfly").setOrigin(0.5, 0.5).setDepth(D_SPRITE).setVisible(false);

    // ===== Ghost/owner/cake phủ đè lên bg (A) =====
    this.ghostImg = this.add.sprite(0, 0, "ghost").setOrigin(0, 0).setDepth(D_SPRITE).setVisible(false);
    this.ownerImg = this.add.image(0, 0, "owner").setOrigin(0, 0).setDepth(D_SPRITE).setVisible(false);
    this.cakeImg = this.add.sprite(0, 0, "cake").setOrigin(0, 0).setDepth(D_SPRITE).setVisible(false);

    // ===== "!" marks trên đầu mèo (P2-B2: 30px/42px = (10|14)*GX) =====
    this.markText = this.add.text(0, 0, "", {
      fontFamily: "monospace", fontSize: "30px", color: "#ffffff", fontStyle: "bold"
    }).setDepth(D_MARK).setVisible(false);

    // ===== Parallax layers (C — chỉ GARDEN) =====
    if (!this.textures.exists("fx-far")) this.textures.createCanvas("fx-far", 960, 270);
    if (!this.textures.exists("fx-near")) this.textures.createCanvas("fx-near", 1200, 270);
    this.farTex = this.textures.get("fx-far");
    this.nearTex = this.textures.get("fx-near");
    this.farImg = this.add.image(0, 0, "fx-far").setOrigin(0, 0).setDepth(D_FAR).setScrollFactor(0.25).setVisible(false);
    this.nearImg = this.add.image(0, 0, "fx-near").setOrigin(0, 0).setDepth(D_NEAR).setScrollFactor(1.15).setVisible(false);
    this.renderNear(); // vẽ 1 lần (tĩnh)

    // ===== FX + light pool + night tint (B/D — screen-space) =====
    if (!this.textures.exists("fx-tex")) this.textures.createCanvas("fx-tex", 480, 270);
    if (!this.textures.exists("fx-pool")) this.textures.createCanvas("fx-pool", 480, 270);
    this.fxTex = this.textures.get("fx-tex");
    this.poolTex = this.textures.get("fx-pool");
    this.fxImg = this.add.image(0, 0, "fx-tex").setOrigin(0, 0).setDepth(D_FX).setScrollFactor(0).setVisible(false);
    this.poolImg = this.add.image(0, 0, "fx-pool").setOrigin(0, 0).setDepth(D_POOL).setScrollFactor(0).setVisible(false);
    this.tintRect = this.add.rectangle(0, 0, 480, 270, 0x0a0e28, 0).setOrigin(0, 0).setDepth(D_TINT).setScrollFactor(0);

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

    // fade chuyển cảnh (D) — đứng yên khi frozen (visual determinism)
    if (s.scene !== prevScene) this.fadeT = 0.6; // D: fade dài hơn (0.35 → 0.6) + ease-out
    if (this.fadeT > 0 && !s.frozen) this.fadeT -= dt;

    // ===== camera scroll (GARDEN/HALLWAY 320 logical → 960px) + shake MANUAL (C) =====
    // Phaser 4 camera effects (shake/zoomTo) KHÔNG update tự động trong setup này + dùng Math.random
    // (phá determinism) → tự quản lý: scroll offset sin/cos deterministic + zoom lerp theo dt (R-03).
    const sc = camX(s) * 3;
    if (!s.frozen && s.scareActive > 0) {
      const t = time / 1000;
      const amp = s.scareActive >= 4 ? 5 : 3;
      this.cameras.main.setScroll(sc + Math.sin(t * 55) * amp, Math.cos(t * 47) * amp);
    } else {
      this.cameras.main.setScroll(sc, 0);
    }
    if (!s.frozen) {
      const target = s.scareActive === 5 ? 1.04 : 1;
      this._zoom += (target - this._zoom) * Math.min(1, dt * 10);
      if (Math.abs(this._zoom - target) < 0.001) this._zoom = target;
      this.cameras.main.setZoom(this._zoom);
    }

    // ===== Quy tắc frozen (C2v2-17): anims pauseAll + KHÔNG play() khi frozen =====
    if (s.frozen && !this._frozen) {
      this._frozen = true;
      this.anims.pauseAll();
    } else if (!s.frozen && this._frozen) {
      this._frozen = false;
      this.anims.resumeAll();
    }

    // ===== render =====
    // R1: khi s.frozen, đóng băng render time (capture lần đầu) để bg/sprite deterministic
    // (core đã freeze s.time khi frozen → sprite dùng s.time cũng deterministic; riêng drawGarden/drawKitchen...
    //  nhận param `time` từ Phaser loop nên phải freeze thủ công ở đây — AC-13 / visual spec)
    const rtime = s.frozen ? (this._frozenTime ?? (this._frozenTime = time)) : (this._frozenTime = null, time);
    this.renderBg(rtime);
    this.renderParallax(rtime);
    this.renderSprites(rtime);
    this.renderFXLayers(rtime);
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
        // overlay đêm cũ ĐÃ BỎ — thay bằng light pool (T5.5; B) — light pool renderFXLayers
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

  // ===== Parallax (C — chỉ GARDEN): farTex mây redraw mỗi frame bằng rtime (C2-13) =====
  renderParallax(rtime) {
    const s = this.state;
    if (s.scene !== "GARDEN") {
      this.farImg.setVisible(false);
      this.nearImg.setVisible(false);
      return;
    }
    this.farImg.setVisible(true);
    this.nearImg.setVisible(true);
    const d = s.darkness || 0;
    const ctx = this.farTex.getContext();
    ctx.clearRect(0, 0, 960, 270);
    // 3 đám mây lớn style ảnh title — x = [60,260,460] + drift (C2v2-05)
    const xs = [60, 260, 460], ys = [24, 56, 88];
    const alpha = 0.5 + 0.2 - d * 0.4; // mây tối dần theo darkness
    for (let i = 0; i < 3; i++) {
      const mx = xs[i] + Math.sin(rtime * 0.05 + i * 1.3) * 20;
      const col = "rgba(255,255,255," + Math.max(0.15, alpha - i * 0.05).toFixed(3) + ")";
      const shade = "rgba(190,215,240," + Math.max(0.1, alpha - i * 0.05 - 0.15).toFixed(3) + ")";
      const w = 90 + i * 14, h = 26 + i * 4;
      ctx.fillStyle = col;
      ctx.fillRect(Math.round(mx), Math.round(ys[i] + 6), w, h - 6);
      ctx.fillRect(Math.round(mx) + 12, Math.round(ys[i]), w - 24, 6);
      ctx.fillRect(Math.round(mx) + Math.round(w * 0.55), Math.round(ys[i]) - 4, Math.round(w * 0.3), 5);
      ctx.fillStyle = shade;
      ctx.fillRect(Math.round(mx), Math.round(ys[i] + h - 4), w, 4);
    }
    this.farTex.refresh();
  }

  // vẽ nearTex 1 lần (tĩnh — cỏ/hoa tiền cảnh, C2-03: 6 cụm lặp 200px)
  renderNear() {
    const ctx = this.nearTex.getContext();
    ctx.clearRect(0, 0, 1200, 270);
    for (let i = 0; i < 6; i++) {
      const bx = i * 200;
      // cỏ cao (y 76..90 logical = 228..270 px)
      for (let k = 0; k < 6; k++) {
        const gx = bx + 20 + k * 30;
        ctx.fillStyle = k % 2 ? "#3fae4a" : "#58c95f";
        ctx.fillRect(gx, 228, 3, 42);
        ctx.fillRect(gx + 4, 236, 2, 34);
      }
      // hoa nhỏ
      ctx.fillStyle = "#ff6b9d";
      ctx.fillRect(bx + 60, 246, 4, 4);
      ctx.fillStyle = "#ffd93b";
      ctx.fillRect(bx + 150, 238, 4, 4);
    }
    this.nearTex.refresh();
  }

  // ===== FX layers (B/D): fx particles + light pool + night tint (screen-space) =====
  renderFXLayers(rtime) {
    const s = this.state;
    const camXPx = camX(s) * 3;
    // fx particles
    const hasFx = ["GARDEN", "HAUNTED", "BIRTHDAY"].indexOf(s.scene) !== -1;
    this.fxImg.setVisible(hasFx);
    if (hasFx) {
      const ctx = this.fxTex.getContext();
      renderFx(ctx, s, rtime, camXPx);
      this.fxTex.refresh();
    }
    // light pool (ambient α theo scene)
    this.poolImg.setVisible(true);
    const pctx = this.poolTex.getContext();
    renderLightPool(pctx, s, rtime, camXPx);
    this.poolTex.refresh();
    // night tint (chỉ GARDEN — C2v2-02/R-01)
    this.tintRect.setAlpha(nightTintAlpha(s));
  }

  // ===== Sprite động (A): sprite sheet PNG + Phaser Animations =====
  renderSprites(rtime) {
    const s = this.state;
    const p = s.player;
    const inGameplay = ["GARDEN", "LIVING", "KITCHEN", "HAUNTED", "HALLWAY", "BIRTHDAY"].indexOf(s.scene) !== -1;

    // ===== player — sheet cat.png, origin 0.5, pos (p.x*3+24, p.y*3+24) (C1-02/C1-03) =====
    if (inGameplay) {
      this.catImg.setPosition(p.x * 3 + 24, p.y * 3 + 24);
      this.catImg.setFlipX(p.dir < 0);
      this.catImg.setVisible(true);
      if (!s.frozen) { // C2v2-17: frozen → không play(), giữ frame hiện tại
        if (p.moving) {
          if (this.catImg.anims.getName() !== "cat-walk") this.catImg.play("cat-walk", true);
        } else {
          if (this.catImg.anims.getName() !== "cat-idle-cycle") this.catImg.play("cat-idle-cycle", true, 0, true);
        }
      } else if (this.catImg.anims.currentAnim && this.catImg.anims.getName() === "cat-idle-cycle") {
        // frozen: giữ nguyên playhead (pauseAll đã chặn) — không gì phải làm
      }
    } else {
      this.catImg.setVisible(false);
    }

    // ===== butterfly — sheet butterfly.png (C2v2-06: bướm 8×6 ở tâm frame) =====
    if (s.scene === "GARDEN" && s.butterfly) {
      const b = s.butterfly;
      this.bfImg.setPosition(b.x * 3, b.y * 3);
      this.bfImg.setVisible(true);
      if (!s.frozen) {
        if (this.bfImg.anims.getName() !== "bfl-flutter") this.bfImg.play("bfl-flutter", true);
      }
    } else {
      this.bfImg.setVisible(false);
    }

    // ===== ghost (HAUNTED — mirror vendor: phase !== H_INIT || !dialogue) =====
    const ghostVisible = s.scene === "HAUNTED" && (s.phase !== "H_INIT" || !s.dialogue);
    if (ghostVisible) {
      this.ghostImg.setPosition(136 * 3, (14 + Math.sin(rtime * 2)) * 3); // bob deterministic (C2-10)
      this.ghostImg.setAlpha(s.darkness > 0.5 ? 0.85 : 1); // C3-01
      this.ghostImg.setVisible(true);
      if (!s.frozen) {
        if (this.ghostImg.anims.getName() !== "ghost-float") this.ghostImg.play("ghost-float", true);
      }
    } else {
      this.ghostImg.setVisible(false);
    }

    // ===== owner (GARDEN G_INIT + BIRTHDAY — C3-08: setMessage set dialogue ✓) =====
    const ownerInGarden = s.scene === "GARDEN" && s.phase === "G_INIT" && s.dialogue;
    const ownerInBirthday = s.scene === "BIRTHDAY";
    if (ownerInGarden) {
      this.ownerImg.setPosition(286 * 3, 52 * 3);
      this.ownerImg.setVisible(true);
    } else if (ownerInBirthday) {
      this.ownerImg.setPosition(96 * 3, 42 * 3);
      this.ownerImg.setVisible(true);
    } else {
      this.ownerImg.setVisible(false);
    }

    // ===== cake (BIRTHDAY — (70,40) che trọn nến+lửa vendor, C1-06) =====
    if (s.scene === "BIRTHDAY") {
      this.cakeImg.setPosition(70 * 3, 40 * 3);
      this.cakeImg.setVisible(true);
      if (!s.frozen) {
        if (this.cakeImg.anims.getName() !== "cake-flame") this.cakeImg.play("cake-flame", true);
      }
    } else {
      this.cakeImg.setVisible(false);
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
    // fade chuyển cảnh (D: ease-out — fadeT 0.6s, alpha (fadeT/0.6)² × 0.75)
    this.fadeRect.setAlpha(fadeAlpha(this.fadeT));
  }
}
