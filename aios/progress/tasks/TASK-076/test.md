# TASK-076 — Test (kết quả thật)

> Ngày: 2026-08-15 · Docs-only task — test = script validate cấu trúc + Mermaid parse thật + đối chiếu dữ liệu.

## 1. Script validate cấu trúc + dữ liệu (`implementation/validate-v3.js`)

Chạy: `node aios/progress/tasks/TASK-076/implementation/validate-v3.js`

**Kết quả: 19/19 PASS** ✅

| # | Check | Kết quả |
|---|-------|---------|
| AC2 | ≥ 8 khối ```mermaid (12 khối: 10 flowchart + 1 stateDiagram-v2 + 1 sequenceDiagram) | ✅ |
| AC11 | Khối 4 plane (Autonomy/Control/Worker/Execution) | ✅ |
| AC11 | Khối Decision Pipeline (Normalizer/Rule Engine/Workflow Matcher/Planner LLM) | ✅ |
| AC11 | Khối luồng 12 bước (Policy pre-check/ResourceService/ExecutionService/AgentSelector/CapabilityRouter) | ✅ |
| AC11 | Khối Runtime Kernel đủ 9 services | ✅ |
| AC11 | Khối Core Intelligence 6 năng lực | ✅ |
| AC5 | Đủ INV-001..034 | ✅ |
| AC5 | 5 release gates (Gate A–E) | ✅ |
| AC5 | Tuyên bố freeze (release blocker) | ✅ |
| AC3 | M10 DONE — 1939 tests / conformance READY / doctor 100/100 / review ACCEPTED | ✅ |
| AC4 | Đủ 13 task M10 trong bảng (ánh xạ id đúng PROGRESS) | ✅ |
| AC6 | Đủ module M10 (freeze/constitution/contract/hardening/durable/slo/safety/kill/security/doctor/dashboard/performance/certification/migration) | ✅ |
| AC7 | Spot-check milestones M1/M5/M7/M9/M8 khớp số liệu | ✅ |
| AC13 | Bảng tasks M1–M9 khớp v2 §11.1 (mọi dòng v2 có trong v3) | ✅ |
| P3-2 | Bảng milestones M0–M9 khớp v2 | ✅ |
| AC2 | Không dùng gantt | ✅ |

> 2 fail đầu tiên do script chọn sai phạm vi (khối 4 plane trùng tên "CONTROL PLANE" với khối 7 tầng; AC13 trích toàn file v2 thay vì §11.1 theo spec) → **đã sửa script**, không phải lỗi nội dung v3.

## 2. Validate Mermaid parse thật (`implementation/validate-mermaid.mjs`) — AC8

Chuẩn bị: `npm install --prefix aios/tools/mermaid-validate mermaid jsdom --no-save` (149 packages, 19s — có network, chạy trên Windows thuần, không cần chromium).
Chạy: `node aios/progress/tasks/TASK-076/implementation/validate-mermaid.mjs`

**Kết quả: 12/12 khối parse OK** ✅ — mọi khối flowchart/stateDiagram-v2/sequenceDiagram đều parse không lỗi bằng `mermaid.parse()` (mermaid v11 + jsdom).

## 3. AC9 — git diff xác nhận v2 chỉ đổi header/§0/§14

`git diff --stat docs/architecture-v2.md` → 9 dòng thay đổi (7 insertions/4 deletions) — toàn bộ nằm trong: header (2 dòng), §0 (1 dòng thêm cảnh báo), §14 (2 dòng). ✅

## 4. AC12 — `docs/architecture/*` không đổi

`git status --short docs/architecture/` → không có output (6 file frozen nguyên vẹn). ✅

## Kết luận

**13/13 AC — TASK-076 PASS** ✅ (19/19 cấu trúc + 12/12 Mermaid parse + AC9 + AC12).
