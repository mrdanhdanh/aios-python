/* fx.js — TASK-082: hiệu ứng deterministic seeded + light pool + transition (B + D)
 * 100% thuần hàm: mọi output tính từ (time/rtime, state, seed cố định) — KHÔNG Math.random.
 * GameScene truyền rtime (đóng băng khi s.frozen) → visual determinism giữ nguyên.
 * Các hàm nhận `camX` (px) — nguồn sáng world-coord trừ camX (R-02).
 */

// ===== PRNG deterministic (mulberry32) =====
export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** seed số từ chuỗi cố định (FNV-1a) */
export function hashSeed(str) {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// ===== FX state — thuần hàm theo (scene, state, time, camX) =====
/**
 * Trả về danh sách particle (screen-space px, đã trừ camX):
 *  dust: GARDEN ngày (darkness < 0.5) — 14 hạt quanh cây lớn (230,40) + nhà hiên
 *  fireflies: GARDEN đêm (darkness >= 0.5) — 10 chấm #d8ff8a
 *  breath: HAUNTED — 8 chấm sương quanh ghost (139,16)
 *  sparks: BIRTHDAY — 6 tia lửa quanh lò sưởi (8,40) (LIVING không có lò sưởi — C1-07)
 */
export function fxState(scene, s, time, camX) {
  const cx = camX || 0;
  const dust = [], fireflies = [], breath = [], sparks = [];
  const d = s.darkness || 0;

  if (scene === "GARDEN" && d < 0.5) {
    // bụi bay quanh cây lớn (230,40) + nhà hiên (270,50) — R-02: trừ camX
    const spots = [
      [230, 40, 3, 1.1], [230, 40, 3, 1.1], [230, 40, 3, 1.1], [230, 40, 3, 1.1], [230, 40, 3, 1.1], [230, 40, 3, 1.1], [230, 40, 3, 1.1],
      [270, 50, 2, 0.9], [270, 50, 2, 0.9], [270, 50, 2, 0.9], [270, 50, 2, 0.9], [270, 50, 2, 0.9], [270, 50, 2, 0.9], [270, 50, 2, 0.9]
    ];
    for (let i = 0; i < spots.length; i++) {
      const [bx, by, amp, sp] = spots[i];
      const x = bx * 3 - cx + Math.sin(time * sp + i * 1.7) * amp * 4;
      const y = by * 3 + Math.cos(time * sp * 0.8 + i * 2.1) * amp * 3;
      const a = 0.15 + 0.2 * (0.5 + 0.5 * Math.sin(time * 2 + i * 2.3));
      dust.push({ x, y, a, s: 1 + (i % 2) });
    }
  }

  if (scene === "GARDEN" && d >= 0.5) {
    // đom đóm quanh vườn (world 20..300, y 40..60) — trừ camX
    const seeds = [3, 7, 11, 17, 23, 31, 41, 47, 53, 61];
    for (let i = 0; i < 10; i++) {
      const bx = 20 + ((seeds[i] * 29) % 280);
      const by = 40 + ((seeds[i] * 13) % 20);
      const x = bx * 3 - cx + Math.sin(time * 0.5 + i * 2.3) * 6;
      const y = by * 3 + Math.cos(time * 0.4 + i * 1.7) * 4;
      const a = Math.max(0, Math.sin(time * 2 + i * 2.3)) * 0.8;
      fireflies.push({ x, y, a });
    }
  }

  if (scene === "HAUNTED") {
    // hơi thở ma quanh ghost (139,16) — trừ camX (HAUNTED camX=0 nhưng giữ nhất quán)
    for (let i = 0; i < 8; i++) {
      const x = 139 * 3 - cx + Math.sin(time * 1.2 + i * 1.9) * 10;
      const y = 22 * 3 + Math.cos(time * 0.9 + i * 2.7) * 6;
      const a = 0.05 + 0.1 * (0.5 + 0.5 * Math.sin(time * 1.6 + i * 3.1));
      breath.push({ x, y, a });
    }
  }

  if (scene === "BIRTHDAY") {
    // tia lửa lò sưởi (8,40) — bay lên rồi tan
    for (let i = 0; i < 6; i++) {
      const phase = (time * 0.8 + i * 0.35) % 1;
      const x = 14 * 3 - cx + Math.sin(time * 3 + i * 2.2) * 4;
      const y = (40 * 3 - 6) - phase * 26;
      const a = Math.max(0, 0.5 - phase * 0.5);
      sparks.push({ x, y, a });
    }
  }

  return { dust, fireflies, breath, sparks };
}

// ===== Render particles vào CanvasTexture (screen-space 480×270) =====
export function renderFx(ctx, s, time, camX) {
  const st = fxState(s.scene, s, time, camX);
  ctx.clearRect(0, 0, 480, 270);
  for (const p of st.dust) { ctx.fillStyle = "rgba(255,244,214," + p.a.toFixed(3) + ")"; ctx.fillRect(Math.round(p.x), Math.round(p.y), p.s, p.s); }
  for (const p of st.fireflies) { ctx.fillStyle = "rgba(216,255,138," + p.a.toFixed(3) + ")"; ctx.fillRect(Math.round(p.x), Math.round(p.y), 2, 2); }
  for (const p of st.breath) { ctx.fillStyle = "rgba(220,235,255," + p.a.toFixed(3) + ")"; ctx.fillRect(Math.round(p.x), Math.round(p.y), 2, 2); }
  for (const p of st.sparks) { ctx.fillStyle = "rgba(255,140,28," + p.a.toFixed(3) + ")"; ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1); }
}

// ===== Light pool (thay overlay đêm phẳng — C2-02) =====
// ambient α theo scene; radial gradients trong suốt quanh nguồn sáng (world trừ camX).
export function ambientAlpha(scene, s) {
  switch (scene) {
    case "GARDEN": return Math.max(0, ((s.darkness || 0) - 0.5) * 0.75); // 0..0.375
    case "HAUNTED": return 0.28;
    case "LIVING": return 0.15;
    case "BIRTHDAY": return 0.12;
    case "HALLWAY": return 0.12; // R-06: nhẹ + đuốc tường
    default: return 0;
  }
}

// nguồn sáng: [x world logical, y world logical, bán kính px, alpha đỉnh, scale]
function lightSources(scene) {
  const G = 3;
  switch (scene) {
    case "GARDEN":
      return [
        ["player", 0, 0, 90, 0.9],
        [287, 47, 12, 0.85], [271, 46, 20, 0.5], [300, 46, 20, 0.5]
      ];
    case "HAUNTED":
      return [[139, 20, 40, 0.7], [120, 16, 30, 0.5]];
    case "LIVING":
      return [[10, 10, 40, 0.7], [138, 10, 40, 0.7], [82, 16, 25, 0.4]];
    case "BIRTHDAY":
      return [[8, 40, 60, 0.8], [80, 44, 25, 0.6]];
    case "HALLWAY":
      // đuốc tường 11 cái (khớp vendor drawHallway: tx = 8 + i*29, y 10..12)
      return Array.from({ length: 11 }, (_, i) => [8 + i * 29, 10, 25, 0.5]);
    default:
      return [];
  }
}

export function renderLightPool(ctx, s, time, camX) {
  const scene = s.scene;
  const cx = camX || 0;
  const a = ambientAlpha(scene, s);
  ctx.clearRect(0, 0, 480, 270);
  if (a <= 0) return;
  // lớp tối
  ctx.fillStyle = "rgba(8,10,30," + a.toFixed(3) + ")";
  ctx.fillRect(0, 0, 480, 270);
  // gradient sáng (clear) quanh nguồn sáng
  const srcs = lightSources(scene);
  for (const src of srcs) {
    let x, y, r, pa;
    if (src[0] === "player") {
      const p = s.player || { x: 80, y: 60 };
      x = p.x * 3 - cx; y = p.y * 3;
      r = src[3]; pa = src[4];
    } else {
      x = src[0] * 3 - cx; y = src[1] * 3;
      r = src[2]; pa = src[3];
    }
    if (x < -r || x > 480 + r || y < -r || y > 270 + r) continue; // ngoài màn — skip (tối ưu + tránh lệch)
    const g = ctx.createRadialGradient(x, y, 2, x, y, r);
    g.addColorStop(0, "rgba(0,0,0," + pa.toFixed(3) + ")");
    g.addColorStop(0.5, "rgba(0,0,0," + (pa * 0.45).toFixed(3) + ")");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  // ngọn lửa nến/lò sưởi nhấp nháy nhẹ (deterministic theo time)
  void time;
}

// ===== Night tint (D — R-01 guard) =====
// Chỉ GARDEN. darkness = 1 - timers.dark/5 → darkness >= 0.5 khi timers.dark <= 2.5.
export function nightTintAlpha(s) {
  if (!s || s.scene !== "GARDEN") return 0;
  const t = s.timers && s.timers.dark !== undefined ? s.timers.dark : 5 * (1 - (s.darkness || 0));
  return clamp((2.5 - t) / 1.5, 0, 1) * 0.18;
}

// ===== Fade transition ease-out (D) =====
export function fadeAlpha(fadeT) {
  return fadeT > 0 ? Math.pow(fadeT / 0.6, 2) * 0.75 : 0;
}

// ===== Seed cố định cho future fx (giữ API PRNG dùng được — AC-7) =====
export const FX_SEED = hashSeed("yuniebel-phaser-t082");
