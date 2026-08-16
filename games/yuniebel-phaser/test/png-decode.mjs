/* png-decode.mjs — TASK-082: decode PNG buffer → {w, h, px: Uint8Array RGBA}
 * Dùng chung: sprite-sheet.test.js (file) + visual.spec.js (screenshot buffer).
 * 0 dependency — zlib.inflateSync + parse chunks.
 */
import zlib from "node:zlib";

export function decodePNG(buf) {
  const sig = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
  for (let i = 0; i < 8; i++) {
    if (buf[i] !== sig[i]) throw new Error("Not a PNG");
  }
  let off = 8;
  let w = 0, h = 0, idat = [], colorType = 6;
  while (off < buf.length) {
    const len = buf.readUInt32BE(off);
    const type = buf.toString("ascii", off + 4, off + 8);
    const data = buf.subarray(off + 8, off + 8 + len);
    if (type === "IHDR") {
      w = data.readUInt32BE(0);
      h = data.readUInt32BE(4);
      colorType = data[9];
    } else if (type === "IDAT") {
      idat.push(data);
    }
    off += 12 + len;
  }
  const bpp = colorType === 6 ? 4 : 3; // RGBA | RGB
  const stride = w * bpp;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const px = new Uint8Array(w * h * 4);
  const prev = new Uint8Array(stride); // hàng trước (unfiltered)
  const cur = new Uint8Array(stride);
  for (let y = 0; y < h; y++) {
    const row = y * (stride + 1);
    const filter = raw[row];
    cur.fill(0);
    // copy bytes đã filter vào cur
    for (let i = 0; i < stride; i++) cur[i] = raw[row + 1 + i];
    for (let i = 0; i < stride; i++) {
      const a = i >= bpp ? cur[i - bpp] : 0;
      const b = prev[i];
      const c = i >= bpp ? prev[i - bpp] : 0;
      let v = cur[i];
      switch (filter) {
        case 0: break; // None
        case 1: v = (v + a) & 0xff; break; // Sub
        case 2: v = (v + b) & 0xff; break; // Up
        case 3: v = (v + ((a + b) >> 1)) & 0xff; break; // Average
        case 4: { // Paeth
          const p = a + b - c;
          const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
          v = (v + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c)) & 0xff;
          break;
        }
        default: throw new Error("Unsupported PNG filter: " + filter);
      }
      cur[i] = v;
      px[y * stride + i] = v;
    }
    prev.set(cur);
  }
  return { w, h, px };
}
