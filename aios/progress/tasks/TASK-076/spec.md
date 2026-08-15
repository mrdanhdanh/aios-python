# TASK-076 — Architecture v3 (Mermaid): AIOS 1.0 Final

> **Spec (2026-08-15)** — theo yêu cầu người dùng: "vẽ lại kiến trúc hệ thống" + chọn phương án "2 và 3": **(2) vẽ lại kiểu Mermaid** (render được trên GitHub/VS Code preview — thay thế quy ước markdown-thuần của v2) và **(3) tạo file mới riêng** cho bản "AIOS 1.0 Final" (khác tên `architecture-v2.md`). TASK-063 (v1) đã tạo `docs/architecture-v2.md` (markdown thuần, phản ánh M10 `todo`); bản v3 phải phản ánh **M10 DONE — AIOS 1.0 CERTIFIED** (1939 tests, conformance READY).

## Mục tiêu

Tạo `docs/architecture-v3.md` — tài liệu kiến trúc **AIOS 1.0 Final** dùng **Mermaid diagrams** (flowchart/sequenceDiagram/stateDiagram-v2), phản ánh trạng thái cuối: M0–M10 đều done, INV-001..034 frozen (release blocker), bổ sung toàn bộ module M10 (Contract 1.0, Hardening, Durable Execution, SLO, Autonomy Safety, Kill Switch, Security Baseline, Doctor DX, Dashboard 1.0, Performance & Cost, Certification Suite, Migration 1.0).

## Bối cảnh / Lý do

- `docs/architecture-v2.md` (TASK-063, markdown thuần, ASCII) hiện **lỗi thời**: header ghi "M10 — AIOS 1.0 (todo)", §15.2 ghi 12/13 task M10 là `🔲 todo` — nhưng theo `aios/progress/PROGRESS.md` (2026-08-15) **M10 đã DONE 13/13 task**: full suite **1939 pass** + vitest 13/13 + `aiagent conformance` → **AIOS 1.0 READY** + doctor 100/100 + review ACCEPTED.
- Người dùng muốn bản vẽ trực quan hơn (Mermaid) và tách thành file mới — không ghi đè v2 (v2 giữ làm lịch sử, cùng quy ước với `docs/architecture.md`).

## Phạm vi

- Tạo file mới `docs/architecture-v3.md` (Mermaid, AIOS 1.0 Final) với:
  1. Header + cách đọc tài liệu (cập nhật: v3 = hiện hành, v2 = lịch sử)
  2. **Sơ đồ Mermaid tổng quan — đúng 7 tầng L1..L7 theo `docs/architecture/layer-model.md` (FROZEN)**: L1 UI/SDK/API → L2 Autonomy Control → L3 Orchestrator Control Plane → L4 Workflow/Agent/Capability → L5 Runtime Kernel → L6 Tools/State/Events → L7 Infra. Ghi chú rõ: Harness/Enterprise/Ecosystem = lớp mở rộng (thuộc L7); **Autonomous = L2 — KHÔNG phải lớp mở rộng** (v2 sai điểm này); M9 = milestone phát triển L2. Nhóm đảm bảo M10 (Freeze/Harden/Secure/Productize/Certify) = ghi chú, **KHÔNG phải tầng L8**
  3. **Sơ đồ Mermaid 4 plane**: Autonomy → Control → Worker → Execution
  4. **Sơ đồ Mermaid Decision Pipeline 4 tầng**: Normalizer → Rule Engine → Workflow Matcher → Planner LLM
  5. **Sơ đồ Mermaid luồng request 12 bước**: User → FastAPI → Orchestrator → Policy → Resource → Execution → Agent → Capability → Tool → Infra → kết quả + Observability
  6. **Sơ đồ Mermaid Runtime Kernel 9 services**
  7. **Sơ đồ Mermaid Core Intelligence (M5)**: Memory Coordinator → Context Optimizer → Model Router → Planning → Execution Graph → Parallel Scheduler
  8. **Sơ đồ Mermaid M10 — 13 module**: Freeze (Constitution + INV-001..034) · Contract 1.0 · Hardening · Durable · SLO · Safety chain · Kill Switch · Security · Doctor · Dashboard 1.0 · Performance/Cost · Certification (5 gates) · Migration
  9. **Sơ đồ Mermaid timeline milestones** (flowchart, M0→M10 — KHÔNG dùng gantt vì chỉ có 1 mốc ngày thật 2026-08-15) + `stateDiagram-v2` (Safety chain 7 bước: Action Proposal → Risk → Governor → Policy → Permission → Capability → Tool) + `sequenceDiagram` (Kill Switch: user → CLI → kill_switch → execution)
  10. Bảng milestones M0–M10 (M10 = done, số liệu thật), bảng tasks M1–M9 (giữ nguyên số liệu từ v2 — khớp PROGRESS.md), **bảng tasks M10 (13 task, đều done — bổ sung mới)**
  11. INV-001..034 frozen — bảng đầy đủ + 5 release gates (Gate A–E) + tuyên bố **AIOS 1.0 READY/CERTIFIED**
  12. Nguồn & lịch sử (v3 hiện hành; v2 + architecture.md = lịch sử) + ghi lý do đảo quy ước Mermaid (quyết định người dùng 2026-08-15: render GitHub/VS Code preview)
- Cập nhật nhẹ `docs/architecture-v2.md`: **header** (dòng 2–7) đổi "📌 TÀI LIỆU HIỆN HÀNH" → "📜 TÀI LIỆU LỊCH SỬ — thay bằng `architecture-v3.md` (Mermaid, AIOS 1.0 Final, 2026-08-15)" + sửa luôn dòng "Định dạng: markdown thuần — không dùng Mermaid..." thành ghi chú lịch sử ("quy ước cũ; từ v3 dùng Mermaid") + §0 + §14 dẫn chiếu — KHÔNG đổi nội dung khác (git diff kiểm tra).

## Ngoài phạm vi

- Không đổi code backend, không đổi PLAN.md, không đổi các file `docs/architecture/*` (đã frozen ở TASK-063).
- Không xóa/sửa nội dung lịch sử của v2 (chỉ thêm dòng dẫn chiếu).

## Input (nguồn sự thật)

- `docs/architecture-v2.md` — cấu trúc + dữ liệu M0–M9 (khớp PROGRESS.md)
- `aios/progress/PROGRESS.md` (2026-08-15) — M10 DONE: 1939 pass, conformance READY, doctor 100/100
- `aios/progress/LOG.md` — entries M10 (TASK-063..075, module thật mỗi task)
- `docs/PLAN.md` §M10 — 5 gates, 7 layers, Constitution
- `docs/architecture/AIOS-1.0.md` — kiến trúc 1.0 đã freeze (đối chiếu nội dung)

## Output

- `docs/architecture-v3.md` (file chính — Mermaid)
- `docs/architecture-v2.md` (thêm dòng dẫn chiếu v3)
- `aios/progress/tasks/TASK-076/` — hard gate đủ 8-file
- Cập nhật `aios/progress/LOG.md` + `PROGRESS.md` + commit

## Tiêu chí chấp nhận (AC)

| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | Tồn tại `docs/architecture-v3.md`; v2 không bị xóa (còn trong repo) | Tồn tại file |
| AC2 | Có **≥ 8 khối ` ```mermaid `** hợp lệ — gồm flowchart + sequenceDiagram + stateDiagram-v2 (KHÔNG dùng gantt — thiếu ngày thật) | Script đếm + validate |
| AC3 | Header + §Milestones phản ánh **M10 DONE** (13/13 task, 1939 tests, conformance → AIOS 1.0 READY, doctor 100/100, review ACCEPTED) | Đọc + grep |
| AC4 | Có bảng tasks M10: 13 task (TASK-063..075) đều `done` với module thật — **theo đúng ánh xạ id↔module của PROGRESS.md** (thứ tự id thật: 063,064,065,066,069,067,068,070,071,072,075,073,074 — KHÔNG theo thứ tự số liên tục) | Đối chiếu PROGRESS.md |
| AC5 | Đủ INV-001..034 + 5 release gates (Gate A–E) + tuyên bố freeze (vi phạm = release blocker) | Script grep |
| AC6 | Bổ sung đủ module M10 vào sơ đồ/nội dung: freeze/constitution, contract, hardening, durable, slo, safety, kill_switch, security, doctor, dashboard 1.0, performance, certification, migration | Grep từ khóa |
| AC7 | Dữ liệu số liệu (tests/coverage/task id) đối chiếu PROGRESS.md khớp; **coverage M10 = N/A** (không bịa số) | Script đối chiếu |
| AC8 | Mermaid **parse không lỗi** bằng npm package `mermaid` + `jsdom` (vẫn pure JS, không cần chromium, chạy được trên Windows thuần) hoặc `@mermaid-js/parser` (Langium, Node thuần không cần DOM) — `mermaid.parse()` từng block; nếu npm offline: dùng fallback (fence đủ + keyword dòng đầu hợp lệ + subgraph cân bằng + label ký tự đặc biệt đặt trong `""`) VÀ ghi rõ trong evaluation.md rằng validate cú pháp đầy đủ chưa chạy được. Cài npm ở thư mục validate riêng `aios/tools/mermaid-validate/` (KHÔNG commit node_modules, không ô nhiễm dashboard/extension deps) | Test thật |
| AC9 | `docs/architecture-v2.md`: header đổi thành "📜 TÀI LIỆU LỊCH SỬ" + dòng dẫn chiếu v3; **git diff xác nhận v2 CHỈ đổi header/§0/§14** (không đổi nội dung khác) | Đọc + git diff |
| AC10 | Đóng DoD: LOG.md + PROGRESS.md + commit | Checklist AGENTS.md §3.1 |
| AC11 | Mỗi sơ đồ bắt buộc có từ khóa đặc trưng — **grep THEO KHỐI ` ```mermaid `** (tách từng khối, không grep toàn file — tránh false-positive): khối 4 plane chứa Autonomy/Control/Worker/Execution; khối Decision Pipeline chứa Normalizer/Rule Engine/Workflow Matcher/Planner LLM; khối luồng request chứa Policy pre-check/ResourceService/ExecutionService/AgentSelector/CapabilityRouter; khối Runtime Kernel chứa đủ 9 services; khối Core Intelligence chứa Memory Coordinator/Context Optimizer/Model Router/Planning Engine/Execution Graph/Parallel Scheduler. Từ khóa xuất hiện **nguyên văn** trong khối | Script grep theo khối |
| AC12 | `docs/architecture/*` (6 file frozen) KHÔNG bị thay đổi — git diff | git diff |
| AC13 | Bảng tasks M1–M9 trong v3 khớp bảng v2 — cách làm: trích các dòng bảng markdown §11.1 của v2 chứa `TASK-0xx` thuộc M1–M9 (bỏ header/separator), normalize whitespace, so sánh set dòng với v3; spot-check 3–5 dòng đối chiếu PROGRESS.md (đề phòng v2 sai thì v3 kế thừa sai) | Script so sánh |

## Ghi chú

- Docs-only (giống TASK-063 v1): test = script validate cấu trúc + đối chiếu dữ liệu + (nếu được) render thử bằng mermaid-cli.
- Đây là lần đầu dự án dùng Mermaid trong tài liệu chính — chấp nhận quyết định người dùng (phương án 2) thay quy ước "markdown thuần" của TASK-063 v1; ghi rõ lý do trong evaluation.
