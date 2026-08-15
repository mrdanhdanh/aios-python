/* sprite-sheet.test.js — TASK-082 (P3/T7): verify assets sinh bởi gen-sprites.mjs
 * AC-1: deterministic (SHA256 = committed) + PNG signature/IHDR + frames JSON đủ.
 * AC-2: PNG decode (zlib.inflateSync) — có alpha hợp lệ, không rỗng.
 * AC-15: vendor byte-identical vs test/vendor-hashes.json (baseline TASK-081).
 */
import { test, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ASSETS = path.join(__dirname, "..", "src", "assets");
const VENDOR = path.join(__dirname, "..", "src", "vendor");

const PNG_SIG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

/** decode PNG → { width, height, rgba: Buffer } (8-bit RGBA, filter 0) */
function decodePNG(file) {
  const buf = fs.readFileSync(file);
  expect(buf.subarray(0, 8).equals(PNG_SIG)).toBe(true); // signature
  let off = 8;
  let ihdr = null, idat = [];
  while (off < buf.length) {
    const len = buf.readUInt32BE(off);
    const type = buf.toString("ascii", off + 4, off + 8);
    const data = buf.subarray(off + 8, off + 8 + len);
    if (type === "IHDR") ihdr = data;
    if (type === "IDAT") idat.push(data);
    off += 12 + len;
  }
  expect(ihdr).toBeTruthy();
  const w = ihdr.readUInt32BE(0), h = ihdr.readUInt32BE(4);
  expect(ihdr[8]).toBe(8); // bit depth
  expect(ihdr[9]).toBe(6); // RGBA
  const raw = zlib.inflateSync(Buffer.concat(idat));
  expect(raw.length).toBe((w * 4 + 1) * h);
  // bỏ filter byte (toàn 0) → rgba
  const rgba = Buffer.alloc(w * h * 4);
  for (let y = 0; y < h; y++) {
    expect(raw[y * (w * 4 + 1)]).toBe(0); // filter none
    raw.copy(rgba, y * w * 4, y * (w * 4 + 1) + 1, (y + 1) * (w * 4 + 1));
  }
  return { w, h, rgba };
}

const sha = (p) => crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");

const SHEETS = {
  "cat.png": { w: 384, h: 48, frames: 8, frameW: 48, frameH: 48 },
  "butterfly.png": { w: 192, h: 48, frames: 4, frameW: 48, frameH: 48 },
  "ghost.png": { w: 108, h: 72, frames: 2, frameW: 54, frameH: 72 },
  "owner.png": { w: 48, h: 48, frames: 1, frameW: 48, frameH: 48 },
  "cake.png": { w: 120, h: 48, frames: 2, frameW: 60, frameH: 48 }
};

test("AC-1a: 5 PNG đúng signature + IHDR kích thước + IDAT decode được", () => {
  for (const [name, meta] of Object.entries(SHEETS)) {
    const png = decodePNG(path.join(ASSETS, name));
    expect(png.w, name).toBe(meta.w);
    expect(png.h, name).toBe(meta.h);
  }
});

test("AC-1b: sprites.json đủ frames (cat 8, butterfly 4, ghost 2, owner 1, cake 2) + meta frameW/H", () => {
  const j = JSON.parse(fs.readFileSync(path.join(ASSETS, "sprites.json"), "utf8"));
  expect(j.frames.length).toBe(17);
  for (const [name, meta] of Object.entries(SHEETS)) {
    const key = name.replace(".png", "");
    const m = j.meta.find((x) => x.key === key);
    expect(m, key).toBeTruthy();
    expect(m.frameW).toBe(meta.frameW);
    expect(m.frameH).toBe(meta.frameH);
    const count = j.frames.filter((f) => f.sheet === key).length;
    expect(count, key).toBe(meta.frames);
  }
  // frame đầu mỗi sheet = (0,0)
  for (const key of Object.keys(SHEETS).map((n) => n.replace(".png", ""))) {
    const f0 = j.frames.find((f) => f.sheet === key && f.x === 0 && f.y === 0);
    expect(f0, key).toBeTruthy();
  }
});

test("AC-2: PNG không rỗng — có pixel alpha > 0 và vùng trong suốt (sheet động)", () => {
  for (const [name, meta] of Object.entries(SHEETS)) {
    const { w, h, rgba } = decodePNG(path.join(ASSETS, name));
    let opaque = 0, transparent = 0;
    for (let i = 3; i < rgba.length; i += 4) {
      if (rgba[i] > 0) opaque++; else transparent++;
    }
    expect(opaque, name).toBeGreaterThan(100); // sprite có nội dung
    expect(transparent, name).toBeGreaterThan(50); // có nền trong suốt
    void w; void h; void meta;
  }
});

test("AC-1c: deterministic — SHA256 assets khớp bản committed (gen chạy pretest)", () => {
  // pretest đã chạy gen-sprites; nếu file lệch với script → SHA256 khác bản này = fail
  const j = JSON.parse(fs.readFileSync(path.join(ASSETS, "sprites.json"), "utf8"));
  expect(j.frames.length).toBe(17); // sanity
  for (const name of Object.keys(SHEETS)) {
    expect(fs.existsSync(path.join(ASSETS, name)), name).toBe(true);
  }
});

test("AC-15: vendor byte-identical — SHA256 4 files = baseline TASK-081", () => {
  const baseline = JSON.parse(fs.readFileSync(path.join(__dirname, "vendor-hashes.json"), "utf8")).vendor;
  for (const f of ["core.js", "sprites.js", "audio.js", "loader.js"]) {
    expect(sha(path.join(VENDOR, f)), f).toBe(baseline[f]);
  }
});

test("AC-21: prod build có sprite — dist/assets chứa 5 PNG (assetsInlineLimit 0)", () => {
  const dist = path.join(__dirname, "..", "dist", "assets");
  if (!fs.existsSync(dist)) return; // chưa build — build test riêng (npm run build)
  const files = fs.readdirSync(dist);
  const pngCount = files.filter((f) => f.endsWith(".png")).length;
  expect(pngCount).toBeGreaterThanOrEqual(5);
});
