/* fx.test.js — TASK-082 (P3/T9): FX deterministic + transition math
 * AC-7: PRNG seeded deterministic, không Math.random trong fx.js (grep).
 * AC-8: fxState theo scene/darkness (bụi GARDEN ngày, đom đóm đêm, hơi thở HAUNTED, tia lửa BIRTHDAY).
 * AC-12: fadeAlpha ease-out. AC-13/AC-23: nightTintAlpha (guard R-01, chỉ GARDEN).
 * AC-9: light pool — ambient α theo scene; nguồn sáng trừ camX.
 */
import { test, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  mulberry32, hashSeed, fxState, renderFx, renderLightPool,
  nightTintAlpha, fadeAlpha, ambientAlpha
} from "../src/fx/fx.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ===== state giả (đủ trường fx dùng) =====
function fakeState(scene, over = {}) {
  return Object.assign({
    scene, darkness: 0,
    timers: {},
    player: { x: 80, y: 60 },
    butterfly: { x: 160, y: 43 }
  }, over);
}

// ===== mock 2D ctx (proxy — không cần canvas thật) =====
function mockCtx() {
  return new Proxy({}, {
    get(t, p) {
      if (p === "createRadialGradient") return () => ({ addColorStop() {} });
      if (typeof p === "string" && (p === "fillRect" || p === "clearRect")) return () => {};
      return t[p];
    },
    set(t, p, v) { t[p] = v; return true; }
  });
}

test("AC-7a: mulberry32 deterministic — cùng seed → cùng chuỗi số", () => {
  const a = mulberry32(42), b = mulberry32(42);
  for (let i = 0; i < 10; i++) expect(a()).toBe(b());
  // seed khác → khác
  const c = mulberry32(43);
  expect(a()).not.toBe(c());
});

test("AC-7b: hashSeed ổn định + khác nhau theo chuỗi", () => {
  const h1 = hashSeed("yuniebel"), h2 = hashSeed("yuniebel");
  expect(h1).toBe(h2);
  expect(h1).toBeGreaterThan(0);
  expect(hashSeed("yuniebel-2")).not.toBe(h1);
});

test("AC-7c: fx.js không dùng Math.random (grep source — loại comment)", () => {
  const src = fs.readFileSync(path.join(__dirname, "..", "src", "fx", "fx.js"), "utf8");
  // bỏ comment dòng //... rồi grep gọi thật (không đếm comment nói về Math.random)
  const code = src.split("\n").filter((l) => !l.trim().startsWith("//") && !l.trim().startsWith("*")).join("\n");
  expect(/Math\.random\s*\(/.test(code)).toBe(false);
});

test("AC-8a: bụi — GARDEN ngày (darkness<0.5) có dust, không fireflies", () => {
  const st = fxState("GARDEN", fakeState("GARDEN", { darkness: 0.2 }), 1, 0);
  expect(st.dust.length).toBe(14);
  expect(st.fireflies.length).toBe(0);
  expect(st.breath.length).toBe(0);
  expect(st.sparks.length).toBe(0);
});

test("AC-8b: đom đóm — GARDEN đêm (darkness>=0.5) có fireflies, không dust", () => {
  const st = fxState("GARDEN", fakeState("GARDEN", { darkness: 1 }), 1, 0);
  expect(st.fireflies.length).toBe(10);
  expect(st.dust.length).toBe(0);
  expect(st.fireflies.every((f) => f.a >= 0 && f.a <= 0.8)).toBe(true);
});

test("AC-8c: hơi thở ma — HAUNTED có breath", () => {
  const st = fxState("HAUNTED", fakeState("HAUNTED"), 1, 0);
  expect(st.breath.length).toBe(8);
});

test("AC-8d: tia lửa — chỉ BIRTHDAY (LIVING không lò sưởi — C1-07)", () => {
  const b = fxState("BIRTHDAY", fakeState("BIRTHDAY"), 1, 0);
  expect(b.sparks.length).toBe(6);
  const l = fxState("LIVING", fakeState("LIVING"), 1, 0);
  expect(l.sparks.length).toBe(0);
});

test("AC-8e: fxState deterministic — cùng (scene,state,time,camX) → cùng output", () => {
  const s1 = fakeState("GARDEN", { darkness: 0.2 });
  const s2 = fakeState("GARDEN", { darkness: 0.2 });
  const a = fxState("GARDEN", s1, 12.34, 90);
  const b = fxState("GARDEN", s2, 12.34, 90);
  expect(a).toEqual(b);
});

test("AC-8f: camX — nguồn world trừ camX (R-02): dust x giảm đúng 90px", () => {
  const st0 = fxState("GARDEN", fakeState("GARDEN", { darkness: 0.2 }), 1, 0);
  const st1 = fxState("GARDEN", fakeState("GARDEN", { darkness: 0.2 }), 1, 90);
  expect(st1.dust[0].x).toBeCloseTo(st0.dust[0].x - 90, 5);
});

test("AC-12: fadeAlpha ease-out — (fadeT/0.6)² × 0.75", () => {
  expect(fadeAlpha(0)).toBe(0);
  expect(fadeAlpha(0.6)).toBeCloseTo(0.75, 5);
  expect(fadeAlpha(0.3)).toBeCloseTo(0.75 * Math.pow(0.5, 2), 5);
});

test("AC-13: nightTintAlpha — chỉ GARDEN + lerp 1.5s theo timers.dark (C2-01)", () => {
  // timers.dark=2.5 → α 0 (bắt đầu vào đêm); =1.0 → α 0.18 (đầy đủ)
  const s0 = fakeState("GARDEN", { timers: { dark: 2.5 } });
  expect(nightTintAlpha(s0)).toBe(0);
  const s1 = fakeState("GARDEN", { timers: { dark: 1.0 } });
  expect(nightTintAlpha(s1)).toBeCloseTo(0.18, 5);
  const sMid = fakeState("GARDEN", { timers: { dark: 1.75 } });
  expect(nightTintAlpha(sMid)).toBeCloseTo(0.09, 5);
  // không phải GARDEN → 0
  expect(nightTintAlpha(fakeState("HAUNTED", { timers: { dark: 1 } }))).toBe(0);
  expect(nightTintAlpha(fakeState("TITLE"))).toBe(0);
});

test("AC-23: nightTintAlpha guard R-01 — timers.dark undefined → theo darkness, không NaN", () => {
  const sDark = fakeState("GARDEN", { darkness: 1 }); // timers.dark undefined
  expect(Number.isNaN(nightTintAlpha(sDark))).toBe(false);
  expect(nightTintAlpha(sDark)).toBeCloseTo(0.18, 5);
  const sLight = fakeState("GARDEN", { darkness: 0 });
  expect(nightTintAlpha(sLight)).toBe(0);
});

test("AC-9a: ambientAlpha theo scene (C2-02)", () => {
  expect(ambientAlpha("GARDEN", fakeState("GARDEN", { darkness: 0.3 }))).toBe(0);
  expect(ambientAlpha("GARDEN", fakeState("GARDEN", { darkness: 1 }))).toBeCloseTo(0.375, 5);
  expect(ambientAlpha("HAUNTED", fakeState("HAUNTED"))).toBeCloseTo(0.28, 5);
  expect(ambientAlpha("LIVING", fakeState("LIVING"))).toBeCloseTo(0.15, 5);
  expect(ambientAlpha("BIRTHDAY", fakeState("BIRTHDAY"))).toBeCloseTo(0.12, 5);
  expect(ambientAlpha("HALLWAY", fakeState("HALLWAY"))).toBeCloseTo(0.12, 5); // R-06
  expect(ambientAlpha("TITLE", fakeState("TITLE"))).toBe(0);
  expect(ambientAlpha("KITCHEN", fakeState("KITCHEN"))).toBe(0);
});

test("AC-9b: renderLightPool không throw + fill tối khi α>0, không fill khi α=0", () => {
  const ctx = mockCtx();
  let fills = 0;
  const spy = new Proxy({}, {
    get(t, p) {
      if (p === "fillRect") return () => { fills++; };
      if (p === "clearRect") return () => {};
      if (p === "createRadialGradient") return () => ({ addColorStop() {} });
      return t[p];
    },
    set(t, p, v) { t[p] = v; return true; }
  });
  renderLightPool(spy, fakeState("GARDEN", { darkness: 0.2 }), 1, 0); // α=0 → không fill tối
  expect(fills).toBe(0);
  renderLightPool(spy, fakeState("GARDEN", { darkness: 1 }), 1, 0); // α>0 → fill
  expect(fills).toBeGreaterThan(0);
  void ctx;
});

test("renderFx không throw cho mọi scene", () => {
  for (const sc of ["GARDEN", "HAUNTED", "BIRTHDAY", "LIVING", "HALLWAY", "KITCHEN", "TITLE"]) {
    expect(() => renderFx(mockCtx(), fakeState(sc, { darkness: sc === "GARDEN" ? 1 : 0 }), 1, 0)).not.toThrow();
  }
});
