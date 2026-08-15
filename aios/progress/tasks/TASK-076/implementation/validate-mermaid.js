// TASK-076 — validate Mermaid parse (AC8) — dùng mermaid + jsdom (pure JS, không chromium)
// Chạy từ aios/tools/mermaid-validate/: node ../../../progress/tasks/TASK-076/implementation/validate-mermaid.js
const { JSDOM } = require('jsdom');

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', { url: 'http://localhost' });
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..', '..', '..', '..');
const V3 = path.join(ROOT, 'docs', 'architecture-v3.md');
const src = fs.readFileSync(V3, 'utf8');

const blocks = [...src.matchAll(/```mermaid\n([\s\S]*?)```/g)].map(m => m[1]);
console.log(`Tìm thấy ${blocks.length} khối mermaid`);

const mermaid = require('mermaid');
mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });

let pass = 0, fail = 0;
(async () => {
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
})();
