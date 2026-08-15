# TASK-063 — M10-F1: AIOS Architecture 1.0 (Freeze + Constitution) — spec v2

> **Spec v2 (M10-F1, 2026-08-15)**: MỞ RỘNG từ task docs redraw (v1, done) — v1 đã tạo `docs/architecture-v2.md` (kiến trúc hiện hành, markdown thuần, 7/7 AC). v2 bổ sung nội dung M10-F1 theo PLAN.md §M10-3..5: **Architecture Freeze + AIOS Architecture Constitution 1.0 + bộ `docs/architecture/*`**. Phần v1 giữ nguyên (đã done); v2 là phần mở rộng chính thức của M10.

## Mục tiêu (M10-F1)

Chốt kiến trúc 7 layers và freeze toàn bộ Architecture Invariants thành **AIOS Architecture Constitution 1.0** (INV-001..INV-034 — vi phạm = **release blocker**, không còn warning). Sinh bộ tài liệu `docs/architecture/` theo PLAN §M10-4.

## Bối cảnh / Lý do

PLAN.md §M10: "M10 = Freeze Architecture, không phải Freeze Innovation. Sau M10: bug/security/performance fixes, backward-compatible features, ecosystem extensions. Thay đổi fundamental architecture → AIOS 2.0." Hiện INV-001..034 đã được enforcement bằng `backend/tests/test_architecture.py` (79+ arch tests) — cần chốt thành văn bản constitution + tài liệu 7 layers làm chuẩn đối chiếu cho mọi thay đổi sau này.

## Phạm vi (v2)

- Tạo `docs/architecture/AIOS-1.0.md` — kiến trúc 1.0 tổng thể (7 layers + luồng request + tham chiếu module thật)
- Tạo `docs/architecture/layer-model.md` — mô hình 7 tầng đúng thứ tự PLAN §M10-4: `UI/SDK/API · Autonomy Control · Orchestrator Control Plane · Workflow/Agent/Capability · Runtime Kernel · Tools/State/Events · Infra`
- Tạo `docs/architecture/control-plane.md` — Control Plane (Orchestrator + registries + policy + governance)
- Tạo `docs/architecture/execution-plane.md` — Execution Plane (runtime nodes, workers, tools, sandbox)
- Tạo `docs/architecture/autonomy.md` — Autonomy Layer (Goal/Planner/Governor/World)
- Tạo `docs/architecture/constitution-1.0.md` — **AIOS Architecture Constitution 1.0**: 15 core principle (thematic, có mapping canonical INV theo bảng PLAN §M10-5) + bảng ĐỦ INV-001..034 (34 invariant canonical — KHÔNG giảm còn 15 ID) + tuyên bố freeze (vi phạm = release blocker) + renumber note (deferred AIOS 2.0)
- Cập nhật `docs/architecture-v2.md` (section M10 + link tới docs/architecture/)

## Ngoài phạm vi

- Không đổi code backend (test = kiểm tra tài liệu + đối chiếu test_architecture.py)
- Không renumber INV (theo PLAN: deferred AIOS 2.0 — làm renumber = breaking change)
- Không sửa `docs/PLAN.md` (chỉ aios/progress/ theo quy trình)

## Input (nguồn sự thật)

- `docs/PLAN.md` §M10 (7 layers, Constitution 1.0, release gates, golden demo)
- `docs/architecture-v2.md` (kiến trúc hiện hành M0–M9)
- `backend/tests/test_architecture.py` + `backend/src/aios_core/` (cấu trúc module thật)

## Output

- `docs/architecture/AIOS-1.0.md`, `layer-model.md`, `control-plane.md`, `execution-plane.md`, `autonomy.md`, `constitution-1.0.md`
- `aios/progress/tasks/TASK-063/` — hard gate v2 đủ 8-file

## Tiêu chí chấp nhận (AC)

| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | Đủ 5 file `docs/architecture/*` (AIOS-1.0, layer-model, control-plane, execution-plane, autonomy) + constitution-1.0.md | Tồn tại file |
| AC2 | `layer-model.md` mô tả đủ 7 tầng đúng thứ tự PLAN §M10-4 | Đọc + grep |
| AC3 | `constitution-1.0.md` chứa ĐỦ INV-001..INV-034 (34 invariant, nhãn canonical: 001–010, 011–016, 017–021, 022–029, 030–034) + 15 core principle có mapping canonical INV (theo bảng PLAN §M10-5) | Script grep INV-001..034 |
| AC4 | Mọi INV trong constitution ĐỀU có enforcement test trong `backend/tests/test_architecture.py` (grep nhãn `inv001`..`inv034` + `m9_*`) — không invariant "tồn tại trên giấy" | Script đối chiếu tự động |
| AC5 | Constitution tuyên bố freeze: "vi phạm INV = release blocker" + renumber note (deferred AIOS 2.0) | Đọc file |
| AC6 | Markdown thuần (KHÔNG ```mermaid — giữ quy ước v1) | Script kiểm tra |
| AC7 | `docs/architecture-v2.md` được cập nhật (section M10 + link tới docs/architecture/) | Đọc file |
| AC8 | Đóng DoD: LOG.md + PROGRESS.md + commit | Checklist AGENTS.md §3.1 |

## Ghi chú

- Docs-only (v2 giống v1): test = script kiểm tra cấu trúc + đối chiếu INV với test_architecture.py (đảm bảo constitution không chứa invariant chưa được enforce).
- Mapping 15 core principle (PLAN §M10-5): Runtime Isolation=INV-001, Capability Isolation=INV-002, Workflow Independence=INV-003, Tool Independence=INV-004, Control Plane Isolation=INV-005, Contract First=INV-006, Policy First=INV-007, Artifact First=INV-008, Event Driven=INV-009, Deterministic First=INV-010, Autonomous Action Boundary=INV-030, Bounded Autonomy=INV-031, Durable Execution=INV-032, Evaluation Before Improvement=INV-033, Validated Memory Promotion=INV-034.
