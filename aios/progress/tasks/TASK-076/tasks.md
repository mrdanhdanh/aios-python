# TASK-076 — Tasks breakdown

> Checklist chi tiết — theo thứ tự phụ thuộc. Trạng thái cập nhật trong quá trình implement.

## Bước 1 — Chuẩn bị + đọc nguồn (context)

- [x] Đọc `docs/PLAN.md` (master plan) + `aios/progress/PROGRESS.md` + `LOG.md` (đầu phiên)
- [x] Đọc `docs/architecture-v2.md` (cấu trúc + dữ liệu M0–M9)
- [x] Đọc `docs/architecture/layer-model.md` (7 tầng L1–L7 FROZEN)
- [x] Đọc PROGRESS.md phần M10 (13 task done, số liệu 1939/vitest 13/conformance READY/doctor 100)
- [x] Spec TASK-076 + critique-1 + critique-2 resolved

## Bước 2 — Hard gate

- [x] Spec.md (mục tiêu, phạm vi, 13 AC)
- [x] Critique-1.md (2 P1 + 5 P2 + 8 P3 — resolved)
- [x] Critique-2.md (3 P2 + 4 P3 — resolved, đủ 2 vòng)
- [x] tasks.md (file này)
- [ ] review.md (reviewer — pre-implementation APPROVED)
- [ ] → Đủ 8-file hard gate

## Bước 3 — Implement: `docs/architecture-v3.md`

- [ ] Tạo file mới với header "AIOS — Kiến trúc hệ thống (v3 — AIOS 1.0 Final)" + cách đọc (v3 hiện hành, v2/v1 lịch sử, quy ước Mermaid + lý do)
- [ ] **Sơ đồ 1 — flowchart tổng quan 7 tầng L1..L7** (đúng layer-model.md frozen; ghi chú Harness/Enterprise/Ecosystem = L7 mở rộng; Autonomous = L2; M10 = nhóm đảm bảo không phải L8)
- [ ] **Sơ đồ 2 — flowchart 4 plane** (Autonomy → Control → Worker → Execution + INV-030/005 ghi chú)
- [ ] **Sơ đồ 3 — flowchart Decision Pipeline 4 tầng** (Normalizer → Rule Engine → Workflow Matcher → Planner LLM → Execution Plan; 70–90% dừng ở Rule)
- [ ] **Sơ đồ 4 — flowchart luồng request 12 bước** (User → FastAPI → 1–4 → Policy pre-check → Resource → Execution → AgentSelector → CapabilityRouter → Tools → Infra → Kết quả + Observability)
- [ ] **Sơ đồ 5 — flowchart Runtime Kernel 9 services** (9 service + RuntimeKernel DI)
- [ ] **Sơ đồ 6 — flowchart Core Intelligence M5** (Memory Coordinator → Context Optimizer → Model Router → Planning Engine → Execution Graph → Parallel Scheduler → Runtime)
- [ ] **Sơ đồ 7 — flowchart M10 13 module** (Freeze/Constitution, Contract 1.0, Hardening, Durable, SLO, Safety, Kill Switch, Security, Doctor, Dashboard, Performance/Cost, Certification 5 gates, Migration — theo ánh xạ id PROGRESS)
- [ ] **Sơ đồ 8 — flowchart timeline milestones** M0→M10 (số liệu thật, không gantt)
- [ ] **Sơ đồ 9 — stateDiagram-v2 Safety chain** (Action Proposal → Risk → Governor → Policy → Permission → Capability → Tool)
- [ ] **Sơ đồ 10 — sequenceDiagram Kill Switch** (user → CLI → kill_switch → execution/goal)
- [ ] Bảng milestones M0–M10 (M10 done: 1939 tests, conformance READY, doctor 100/100, review ACCEPTED)
- [ ] Bảng tasks M1–M9 (giữ nguyên số liệu v2 — khớp PROGRESS)
- [ ] Bảng tasks M10 (13 task done + module thật + module path)
- [ ] Bảng INV-001..034 (frozen) + 5 release gates (Gate A–E) + tuyên bố AIOS 1.0 READY/CERTIFIED
- [ ] Mục Nguồn & lịch sử (v3 hiện hành; v2 + architecture.md lịch sử; lý do đảo quy ước Mermaid — quyết định người dùng 2026-08-15)

## Bước 4 — Implement: cập nhật `docs/architecture-v2.md`

- [ ] Header (dòng 2–7): "📌 TÀI LIỆU HIỆN HÀNH" → "📜 TÀI LIỆU LỊCH SỬ — thay bằng architecture-v3.md"; dòng "không dùng Mermaid" → ghi chú lịch sử
- [ ] §0 + §14: dẫn chiếu v3
- [ ] Verify git diff: v2 CHỈ đổi header/§0/§14

## Bước 5 — Test (test.md + chạy thật)

- [ ] Script node validate: ≥ 8 khối ```mermaid, mỗi khối keyword đặc trưng (AC11)
- [ ] Validate Mermaid parse (npm mermaid+jsdom hoặc @mermaid-js/parser tại aios/tools/mermaid-validate/); fallback nếu offline → ghi evaluation
- [ ] AC7: đối chiếu số liệu PROGRESS.md (tests/coverage/task id)
- [ ] AC13: so sánh bảng tasks M1–M9 với v2
- [ ] AC12: git diff xác nhận docs/architecture/* không đổi
- [ ] AC9: git diff xác nhận v2 chỉ đổi header/§0/§14
- [ ] AC5: grep INV-001..034 + 5 gates + freeze

## Bước 6 — Evaluate + DoD

- [ ] evaluation.md — đối chiếu 13 AC, bài học, lý do đảo quy ước Mermaid
- [ ] LOG.md entry + PROGRESS.md cập nhật (TASK-076 done)
- [ ] STATS.md nếu cần (không kết thúc milestone → không bắt buộc)
- [ ] Commit (working tree sạch)
