// TASK-076 — validate docs/architecture-v3.md (cấu trúc + dữ liệu + AC)
// Chạy: node validate-v3.js
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..', '..', '..', '..'); // aios/progress/tasks/TASK-076/implementation -> repo root
const V3 = path.join(ROOT, 'docs', 'architecture-v3.md');
const V2 = path.join(ROOT, 'docs', 'architecture-v2.md');

const v3 = fs.readFileSync(V3, 'utf8');
const v2 = fs.readFileSync(V2, 'utf8');

let pass = 0, fail = 0;
const check = (name, ok, detail = '') => {
  if (ok) { pass++; console.log(`  ✅ ${name}`); }
  else { fail++; console.log(`  ❌ ${name} ${detail}`); }
};

// Tách khối mermaid
const blocks = [...v3.matchAll(/```mermaid\n([\s\S]*?)```/g)].map(m => m[1]);
check('AC2: >= 8 khối ```mermaid', blocks.length >= 8, `(found ${blocks.length})`);
console.log(`  → ${blocks.length} khối mermaid`);

// AC11 — grep theo khối (mỗi khối keyword đặc trưng)
const blockHas = (needle) => blocks.some(b => b.includes(needle));
const blkPlane = blocks.findIndex(b => b.includes('AUTONOMY LAYER') && b.includes('WORKER PLANE'));
check('AC11: khối 4 plane (Autonomy/Control/Worker/Execution)', blkPlane >= 0 && ['AUTONOMY', 'CONTROL PLANE', 'WORKER PLANE', 'EXECUTION PLANE'].every(k => blocks[blkPlane].includes(k)));
const blkPipe = blocks.findIndex(b => b.includes('Normalizer'));
check('AC11: khối Decision Pipeline (Normalizer/Rule Engine/Workflow Matcher/Planner LLM)', blkPipe >= 0 && ['Normalizer', 'Rule Engine', 'Workflow Matcher', 'Planner LLM'].every(k => blocks[blkPipe].includes(k)));
const blkFlow = blocks.findIndex(b => b.includes('Policy pre-check'));
check('AC11: khối luồng 12 bước (Policy pre-check/ResourceService/ExecutionService/AgentSelector/CapabilityRouter)', blkFlow >= 0 && ['Policy pre-check', 'ResourceService', 'ExecutionService', 'AgentSelector', 'CapabilityRouter'].every(k => blocks[blkFlow].includes(k)));
const blkKernel = blocks.findIndex(b => b.includes('RuntimeKernel (DI Container)'));
const services9 = ['Execution Service', 'Context Service', 'Event Service', 'Artifact Service', 'Permission Service', 'Policy Service', 'Scheduler Service', 'State Service', 'Resource Service'];
check('AC11: khối Runtime Kernel đủ 9 services', blkKernel >= 0 && services9.every(s => blocks[blkKernel].includes(s)));
const blkIntel = blocks.findIndex(b => b.includes('Memory Coordinator (INV-011)'));
check('AC11: khối Core Intelligence 6 năng lực', blkIntel >= 0 && ['Memory Coordinator', 'Context Optimizer', 'Model Router', 'Planning Engine', 'Execution Graph', 'Parallel Scheduler'].every(k => blocks[blkIntel].includes(k)));

// AC5 — INV-001..034 + 5 gates + freeze
const invs = [...v3.matchAll(/INV-0(\d{2})/g)].map(m => m[1]);
const invSet = new Set(invs);
const allInv = Array.from({ length: 34 }, (_, i) => String(i + 1).padStart(2, '0'));
check('AC5: đủ INV-001..034', allInv.every(id => invSet.has(id)), `(found ${invSet.size}/34)`);
check('AC5: 5 release gates (Gate A-E)', ['Gate A', 'Gate B', 'Gate C', 'Gate D', 'Gate E'].every(g => v3.includes(g)));
check('AC5: tuyên bố freeze (release blocker)', v3.includes('release blocker') && v3.includes('FROZEN'));

// AC3 — M10 DONE
check('AC3: M10 DONE - 1939 tests', v3.includes('1939'));
check('AC3: conformance AIOS 1.0 READY', v3.includes('AIOS 1.0 READY'));
check('AC3: doctor 100/100', v3.includes('100/100'));
check('AC3: review ACCEPTED', v3.includes('review ACCEPTED'));

// AC4 — bảng tasks M10 13 task done
const m10Tasks = ['TASK-063', 'TASK-064', 'TASK-065', 'TASK-066', 'TASK-069', 'TASK-067', 'TASK-068', 'TASK-070', 'TASK-071', 'TASK-072', 'TASK-075', 'TASK-073', 'TASK-074'];
check('AC4: đủ 13 task M10 trong bảng', m10Tasks.every(t => v3.includes(`| ${t} |`)));

// AC6 — module M10 keywords
const m10mods = ['freeze', 'constitution', 'contract', 'hardening', 'durable', 'slo', 'safety', 'kill', 'security', 'doctor', 'dashboard', 'performance', 'certification', 'migration'];
check('AC6: đủ module M10', m10mods.every(k => v3.toLowerCase().includes(k)));

// AC7 — số liệu đối chiếu (spot-check milestones)
const spot = [['428', '95.76'], ['1086', '95.22'], ['1560', '95.05'], ['1780', '94.46'], ['1639']];
check('AC7: spot-check milestones (M1/M5/M7/M9/M8)', spot.every(([a, b]) => v3.includes(a) && (!b || v3.includes(b))));

// AC13 — so sánh bảng tasks M1–M9 với v2 §11.1 (theo spec: chỉ phần §11.1 của v2, không toàn file)
const section = (s, h1, h2) => {
  const i = s.indexOf(h1);
  const j = s.indexOf(h2, i + 1);
  return i >= 0 ? s.slice(i, j > i ? j : undefined) : '';
};
const taskLines = (s) => s.split('\n').filter(l => /\| TASK-0\d{2,3}/.test(l)).map(l => l.trim());
const l2 = taskLines(section(v2, '## 11. Chi tiết tasks M1–M9', '## 12.'));
const l3 = taskLines(section(v3, '## 11. Chi tiết tasks M1–M9', '## 12.'));
const missing = l2.filter(l => !l3.includes(l));
check('AC13: bảng tasks M1-M9 khớp v2 (mọi dòng v2 có trong v3)', missing.length === 0, `(thiếu ${missing.length}: ${missing.slice(0, 3).join(' | ')})`);

// P3-2: spot-check milestones M0-M9 trong bảng
const mB = ['428 tests · 95.76%', '669 tests · 95.51%', '689 pytest + 12 + 19 vitest', '809 tests · 94.92%', '1086 tests · 95.22%', '1521 tests · 95.35%', '1560 tests · 95.05%', '1639 tests', '1780 tests @M9'];
check('P3-2: bảng milestones M0-M9 khớp v2', mB.every(s => v3.includes(s)));

// Số khối loại
const kinds = blocks.map(b => b.trim().split('\n')[0]).filter(k => /^(flowchart|sequenceDiagram|stateDiagram)/.test(k));
console.log(`  → loại sơ đồ: ${kinds.join(', ')}`);
check('AC2: không dùng gantt', !v3.includes('gantt'));

// AC12: docs/architecture/* không đổi — kiểm tra qua git (bên ngoài script, xem phần chạy)
console.log(`\nKẾT QUẢ: ${pass} PASS / ${fail} FAIL`);
process.exit(fail ? 1 : 0);
