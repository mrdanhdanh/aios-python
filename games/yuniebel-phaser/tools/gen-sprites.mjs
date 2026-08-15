#!/usr/bin/env node
/* gen-sprites.mjs — TASK-082: sinh sprite sheet PNG + sprites.json cho Yuniebel's Cat (Phaser 4)
 * 0 dependency: PNG encoder thuần (signature/IHDR/IDAT zlib level 9/IEND + CRC32).
 * Pixel maps dùng đúng rect của vendor sprites.js (palette vendor) — deterministic (cùng input → cùng bytes).
 * Chạy: node tools/gen-sprites.mjs → ghi src/assets/{cat,butterfly,ghost,owner,cake}.png + sprites.json
 */
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "..", "src", "assets");

// ===================== PNG encoder (chuẩn 8-bit RGBA) =====================
const CRC_TABLE = (() => {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c;
  }
  return t;
})();

function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const t = Buffer.from(type, "ascii");
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([t, data])), 0);
  return Buffer.concat([len, t, data, crc]);
}

/** rgba: Buffer (w*h*4) → Buffer PNG hoàn chỉnh */
function encodePNG(w, h, rgba) {
  const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;  // bit depth
  ihdr[9] = 6;  // color type RGBA
  ihdr[10] = 0; // compression
  ihdr[11] = 0; // filter
  ihdr[12] = 0; // interlace
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (w * 4 + 1)] = 0; // filter: none
    rgba.copy(raw, y * (w * 4 + 1) + 1, y * w * 4, (y + 1) * w * 4);
  }
  const idat = zlib.deflateSync(raw, { level: 9 });
  return Buffer.concat([sig, chunk("IHDR", ihdr), chunk("IDAT", idat), chunk("IEND", Buffer.alloc(0))]);
}

// ===================== Grid helpers (logical pixel maps) =====================
function grid(w, h) { return { w, h, p: new Int32Array(w * h).fill(-1) }; }
function set(g, x, y, c) { if (x < 0 || y < 0 || x >= g.w || y >= g.h) return; g.p[y * g.w + x] = c; }
function rect(g, x, y, w, h, c) { for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) set(g, x + i, y + j, c); }

/** grid logical → RGBA Buffer scale×scale (scale=3 → 48×48 từ 16×16) */
function render(g, scale, palette) {
  const w = g.w * scale, h = g.h * scale;
  const buf = Buffer.alloc(w * h * 4);
  for (let y = 0; y < g.h; y++) {
    for (let x = 0; x < g.w; x++) {
      const idx = g.p[y * g.w + x];
      if (idx < 0) continue;
      const [r, gr, b, a] = palette[idx];
      for (let j = 0; j < scale; j++) {
        for (let i = 0; i < scale; i++) {
          const o = ((y * scale + j) * w + (x * scale + i)) * 4;
          buf[o] = r; buf[o + 1] = gr; buf[o + 2] = b; buf[o + 3] = a;
        }
      }
    }
  }
  return buf;
}

// ===================== Palette (vendor sprites.js C — C2-06) =====================
const P = {
  catBody: [0xf5, 0xa6, 0x23, 255], catWhite: [255, 255, 255, 255], catDark: [0xd9, 0x8f, 0x1d, 255],
  catPink: [0xff, 0xb6, 0xc1, 255], eye: [0x1a, 0x1a, 0x2e, 255],
  bflA: [0xe8, 0xc9, 0x3a, 255], bflB: [0xd4, 0xa6, 0x1e, 255], bflC: [0x3c, 0x2a, 0x10, 255],
  ghostBody: [0x8e, 0xc9, 0xff, 230], ghostBodyDim: [0x8e, 0xc9, 0xff, 120], // dithering alpha
  skull: [0xf4, 0xf6, 0xf8, 255], skullShade: [0xb8, 0xc0, 0xc8, 255], black: [0x0a, 0x0a, 0x14, 255],
  hair: [0x7a, 0x4a, 0x21, 255], skin: [0xff, 0xc9, 0xa3, 255], shirt: [0x2e, 0x86, 0xde, 255],
  pants: [0x3d, 0x5a, 0x80, 255], shoes: [0x3c, 0x27, 0x16, 255],
  cake: [0xff, 0xf6, 0xe0, 255], frost: [0xff, 0xc4, 0xe3, 255], cherry: [0xff, 0x9d, 0xb8, 255],
  candle: [0xff, 0x6b, 0x3d, 255], flame: [0xff, 0xd9, 0x3b, 255], flameHot: [0xff, 0x8c, 0x1c, 255]
};
const CAT_PAL = [P.catBody, P.catWhite, P.catDark, P.catPink, P.eye];
const BFL_PAL = [P.bflA, P.bflB, P.bflC];
const GHOST_PAL = [P.ghostBody, P.ghostBodyDim, P.skull, P.skullShade, P.black];
const OWNER_PAL = [P.hair, P.skin, P.shirt, P.pants, P.shoes, P.eye];
const CAKE_PAL = [P.cake, P.frost, P.cherry, P.candle, P.flame, P.flameHot];

// ===================== CAT 16×16 logical ×8 frames (mirror vendor drawCat) =====================
// Vendor rects (sprites.js drawCat): đuôi (12, y+8+tw, 3,2) đậm; thân (3,7,9,7) + bụng (5,10,5,3);
// chân (3,13,2,3)/(9,13,2,3) so le f0/f1; đầu (2,1,11,7) + mặt (4,3,6,3); tai (2,-1,3,3)+(10,-1,3,3)
// tai hồng (3,-1,2,2)/(11,-1,2,2); mắt (4,3,2,2)/(9,3,2,2) + white px; mũi (7,5); ria 4 px.
// R-07.4: dịch xuống 1px (tai y0) — frame 16×16, mèo chiếm trọn (C1-02).
const BODY = 0, WHITE = 1, DARK = 2, PINK = 3, EYE = 4;

function catBase(tw) {
  const g = grid(16, 16);
  const lx = 0; // không flip ở đây — flip qua Phaser setFlipX
  // đuôi (tw = -1, 0, 1 — 2 mức tail0/tail1 + walk giữa)
  rect(g, lx + 12, 8 + tw, 3, 2, DARK);
  // thân + bụng
  rect(g, lx + 3, 7, 9, 7, BODY);
  rect(g, lx + 5, 10, 5, 3, WHITE);
  // đầu + mặt trắng
  rect(g, lx + 2, 1, 11, 7, BODY);
  rect(g, lx + 4, 3, 6, 3, WHITE);
  // tai (dịch 1px xuống)
  rect(g, lx + 2, 0, 3, 3, BODY); rect(g, lx + 10, 0, 3, 3, BODY);
  rect(g, lx + 3, 0, 2, 2, PINK); rect(g, lx + 11, 0, 2, 2, PINK);
  // mắt + mũi + ria
  rect(g, lx + 4, 3, 2, 2, EYE); rect(g, lx + 9, 3, 2, 2, EYE);
  set(g, lx + 4, 3, WHITE); set(g, lx + 9, 3, WHITE);
  set(g, lx + 7, 5, PINK);
  set(g, lx + 1, 4, WHITE); set(g, lx, 5, WHITE);
  set(g, lx + 13, 4, WHITE); set(g, lx + 14, 5, WHITE);
  return g;
}

function catLegs(g, f) {
  // f 0: chân trước BODY, chân sau WHITE (khớp vendor frame 0)
  rect(g, 3, 13, 2, 3, f === 0 ? BODY : WHITE);
  rect(g, 9, 13, 2, 3, f === 1 ? BODY : WHITE);
}

function catBlink(g) {
  // mắt nhắm: thay 2×2 mắt bằng vạch 2×1 màu body đậm hơn (dùng DARK)
  rect(g, 4, 4, 2, 1, DARK);
  rect(g, 9, 4, 2, 1, DARK);
}

const CAT_FRAMES = [
  { name: "walk-0", fn: (g) => { catLegs(g, 0); } },
  { name: "walk-1", fn: (g) => { catLegs(g, 1); } },
  { name: "walk-2", fn: (g) => { catLegs(g, 0); rect(g, 12, 9, 3, 2, DARK); } }, // đuôi thấp hơn
  { name: "walk-3", fn: (g) => { catLegs(g, 1); rect(g, 12, 6, 3, 2, DARK); } }, // đuôi cao hơn
  { name: "idle", fn: (g) => { catLegs(g, 0); } },
  { name: "blink", fn: (g) => { catLegs(g, 0); catBlink(g); } },
  { name: "tail-0", fn: (g) => { catLegs(g, 0); rect(g, 12, 6, 3, 2, DARK); } }, // đuôi cao (sin+)
  { name: "tail-1", fn: (g) => { catLegs(g, 0); rect(g, 12, 10, 3, 2, DARK); } }  // đuôi thấp (sin-)
];

// ===================== BUTTERFLY 16×16 logical (8×6 ở tâm, padding 4×5) ×4 frames =====================
// Vendor: cánh trái (x-2-fr, y-2, 3,3), cánh phải (x+2, y-2, 3+fr, 3), thân dưới (x-1,y+1,2,2)+(x+2,y+1,2,2), px tâm
const BFL_PAL_IDX = { a: 0, b: 1, c: 2 };

function bflFrame(fr) {
  const g = grid(16, 16);
  const ox = 4, oy = 5; // tâm bướm tại (8, 8.5) logical
  const cx = ox + 4, cy = oy + 3;
  rect(g, cx - 2 - fr, cy - 2, 3, 3, BFL_PAL_IDX.a);
  rect(g, cx + 2, cy - 2, 3 + fr, 3, BFL_PAL_IDX.a);
  rect(g, cx - 1, cy + 1, 2, 2, BFL_PAL_IDX.b);
  rect(g, cx + 2, cy + 1, 2, 2, BFL_PAL_IDX.b);
  set(g, cx, cy, BFL_PAL_IDX.c);
  return g;
}

// ===================== GHOST 18×24 logical ×2 frames (đuôi lượn) =====================
// Vendor drawGhostSkull: body (1,2,10,14), (0,4,12,8), (2,16,8,3); sọ (2,4,8,6)+(3,3,2,2)+(7,3,2,2);
// mắt (3,6)+(8,6), mũi (4,8)+(7,8); đuôi (2,19,3±w1,2)+(7,19,3∓w1,2). Ghost trong frame tại offset (3,2).
const GH = { body: 0, dim: 1, skull: 2, shade: 3, black: 4 };
const GOX = 3, GOY = 2;

function ghostBase() {
  const g = grid(18, 24);
  const x = GOX, y = GOY;
  rect(g, x + 1, y + 2, 10, 14, GH.body);
  rect(g, x, y + 4, 12, 8, GH.body);
  rect(g, x + 2, y + 16, 8, 3, GH.body);
  // dithering 2×2 trên thân (alpha thấp — C3-01/C2-06)
  for (let yy = y + 2; yy < y + 19; yy += 2) {
    for (let xx = x; xx < x + 12; xx += 2) {
      if (g.p[yy * 18 + xx] >= 0) set(g, xx + 1, yy, GH.dim);
    }
  }
  // sọ
  rect(g, x + 2, y + 4, 8, 6, GH.skull);
  rect(g, x + 3, y + 3, 2, 2, GH.skull);
  rect(g, x + 7, y + 3, 2, 2, GH.skull);
  set(g, x + 3, y + 6, GH.black); set(g, x + 8, y + 6, GH.black);
  set(g, x + 4, y + 8, GH.black); set(g, x + 7, y + 8, GH.black);
  return g;
}

function ghostTail(g, w1) {
  const x = GOX, y = GOY;
  rect(g, x + 2, y + 19, 3 - w1, 2, GH.body);
  rect(g, x + 7, y + 19, 3 + w1, 2, GH.body);
}

// ===================== OWNER 16×16 logical ×1 (vendor drawOwner tại offset (2,0)) =====================
function ownerFrame() {
  const g = grid(16, 16);
  const x = 2, y = 0;
  rect(g, x + 3, y, 5, 3, 0); // hair
  rect(g, x + 2, y + 2, 7, 3, 0);
  rect(g, x + 4, y + 2, 4, 4, 1); // skin
  set(g, x + 5, y + 3, 5); set(g, x + 7, y + 3, 5); // eyes (đóng — pixel đen)
  set(g, x + 6, y + 5, 2); // nose → shirt màu? vendor dùng #ff6b9d — dùng skin đậm
  rect(g, x + 3, y + 6, 6, 5, 2); // shirt
  rect(g, x + 3, y + 11, 6, 3, 3); // pants
  rect(g, x + 3, y + 14, 2, 2, 4); rect(g, x + 7, y + 14, 2, 2, 4); // shoes
  return g;
}

// ===================== CAKE 20×16 logical ×2 frames (nến cháy flicker) =====================
// Vendor: lửa world y40..42, nến 42..47, frost 46..49, thân 48..54, cherry 50..52 → trong frame y = world-40
const Ck = { cake: 0, frost: 1, cherry: 2, candle: 3, flame: 4, flameHot: 5 };

function cakeBase() {
  const g = grid(20, 16);
  rect(g, 0, 8, 20, 6, Ck.cake);   // thân (world 48..54)
  rect(g, 2, 6, 16, 3, Ck.frost);  // frost (world 46..49)
  rect(g, 6, 10, 8, 2, Ck.cherry); // cherry (world 50..52)
  for (let i = 0; i < 4; i++) rect(g, 4 + i * 4, 2, 1, 5, Ck.candle); // nến (world 42..47)
  rect(g, 0, 14, 20, 2, Ck.cake);  // đế
  return g;
}

function cakeFlame(g, flip) {
  for (let i = 0; i < 4; i++) {
    const hot = (flip ? (i % 2 === 1) : (i % 2 === 0)); // đảo flicker giữa 2 frames
    rect(g, 4 + i * 4, 0, 1, 2, hot ? Ck.flame : Ck.flameHot); // lửa (world 40..42)
  }
}

// ===================== Render + ghi file =====================
function buildCatSheet() {
  const frames = [];
  const buf = Buffer.alloc(384 * 48 * 4); // 8 frames × 48 ngang = 384
  CAT_FRAMES.forEach((f, i) => {
    const g = catBase(0);
    f.fn(g);
    const rgba = render(g, 3, CAT_PAL);
    rgba.copy(buf, i * 48 * 48 * 4);
    frames.push({ name: "cat-" + f.name, x: i * 48, y: 0, w: 48, h: 48 });
  });
  return { buf, w: 384, h: 48, frames, key: "cat", frameW: 48, frameH: 48 };
}

function buildButterflySheet() {
  const frames = [];
  const buf = Buffer.alloc(192 * 48 * 4);
  for (let i = 0; i < 4; i++) {
    const rgba = render(bflFrame(i), 3, BFL_PAL);
    rgba.copy(buf, i * 48 * 48 * 4);
    frames.push({ name: "butterfly-" + i, x: i * 48, y: 0, w: 48, h: 48 });
  }
  return { buf, w: 192, h: 48, frames, key: "butterfly", frameW: 48, frameH: 48 };
}

function buildGhostSheet() {
  const frames = [];
  const buf = Buffer.alloc(108 * 72 * 4);
  for (let i = 0; i < 2; i++) {
    const g = ghostBase();
    ghostTail(g, i === 0 ? -1 : 1);
    const rgba = render(g, 3, GHOST_PAL);
    rgba.copy(buf, i * 54 * 72 * 4);
    frames.push({ name: "ghost-" + i, x: i * 54, y: 0, w: 54, h: 72 });
  }
  return { buf, w: 108, h: 72, frames, key: "ghost", frameW: 54, frameH: 72 };
}

function buildOwnerSheet() {
  const rgba = render(ownerFrame(), 3, OWNER_PAL);
  return { buf: rgba, w: 48, h: 48, frames: [{ name: "owner-0", x: 0, y: 0, w: 48, h: 48 }], key: "owner", frameW: 48, frameH: 48 };
}

function buildCakeSheet() {
  const frames = [];
  const buf = Buffer.alloc(120 * 48 * 4);
  for (let i = 0; i < 2; i++) {
    const g = cakeBase();
    cakeFlame(g, i === 1);
    const rgba = render(g, 3, CAKE_PAL);
    rgba.copy(buf, i * 60 * 48 * 4);
    frames.push({ name: "cake-" + i, x: i * 60, y: 0, w: 60, h: 48 });
  }
  return { buf, w: 120, h: 48, frames, key: "cake", frameW: 60, frameH: 48 };
}

function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const sheets = [buildCatSheet(), buildButterflySheet(), buildGhostSheet(), buildOwnerSheet(), buildCakeSheet()];
  const json = { meta: [], frames: [] };
  for (const s of sheets) {
    const png = encodePNG(s.w, s.h, s.buf);
    const file = path.join(OUT, s.key + ".png");
    fs.writeFileSync(file, png);
    json.meta.push({ key: s.key, sheet: s.key + ".png", frameW: s.frameW, frameH: s.frameH, scale: 3, frames: s.frames.length });
    for (const f of s.frames) json.frames.push({ name: f.name, sheet: s.key, x: f.x, y: f.y, w: f.w, h: f.h });
  }
  fs.writeFileSync(path.join(OUT, "sprites.json"), JSON.stringify(json, null, 2) + "\n");
  // report
  for (const s of sheets) {
    const f = path.join(OUT, s.key + ".png");
    const buf = fs.readFileSync(f);
    const hex = [...buf.slice(0, 8)].map((b) => b.toString(16).padStart(2, "0")).join(" ");
    console.log(`${s.key}.png  ${buf.length} bytes  sig[${hex}]  ${s.w}×${s.h}  frames=${s.frames.length}  sha256=${crypto.createHash("sha256").update(buf).digest("hex")}`);
  }
  const jbuf = fs.readFileSync(path.join(OUT, "sprites.json"));
  console.log("sprites.json  frames=" + json.frames.length + "  sha256=" + crypto.createHash("sha256").update(jbuf).digest("hex"));
}

main();
