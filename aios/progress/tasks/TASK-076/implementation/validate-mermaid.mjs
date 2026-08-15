// TASK-076 — validate Mermaid parse (AC8) — dùng mermaid v11 (ESM) + jsdom
// Chạy: node validate-mermaid.mjs (không cần NODE_PATH — resolve bằng createRequire)
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';

const MV = 'c:/Users/nguye/OneDrive/Desktop/AIAGENT/aios/tools/mermaid-validate';
const require = createRequire(path.join(MV, 'package.json'));

const { JSDOM } = require('jsdom');
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', { url: 'http://localhost' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
// Node 22 có sẵn global navigator — không cần gán

const ROOT = path.resolve(import.meta.dirname, '..', '..', '..', '..', '..');
const V3 = path.join(ROOT, 'docs', 'architecture-v3.md');
const src = fs.readFileSync(V3, 'utf8');

const blocks = [...src.matchAll(/```mermaid\n([\s\S]*?)```/g)].map(m => m[1]);
console.log(`Tìm thấy ${blocks.length} khối mermaid`);

const mermaidMod = await import(pathToFileURL(path.join(MV, 'node_modules', 'mermaid', 'dist', 'mermaid.esm.mjs')));
const mermaid = mermaidMod.default ?? mermaidMod;
mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });

let pass = 0, fail = 0;
for (let i = 0; i < blocks.length; i++) {
  const b = blocks[i];
  const kind = b.trim().split('\n')[0];
  try {
    await mermaid.parse(b);
    pass++;
    console.log(`  ✅ Khối ${i + 1} (${kind}) — parse OK`);
  } catch (e) {
    fail++;
    const msg = String(e.message || e).split('\n').slice(0, 3).join(' | ');
    console.log(`  ❌ Khối ${i + 1} (${kind}) — LỖI: ${msg}`);
  }
}
console.log(`\nKẾT QUẢ: ${pass}/${blocks.length} khối parse OK`);
process.exit(fail ? 1 : 0);
