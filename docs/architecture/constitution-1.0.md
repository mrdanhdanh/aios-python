# AIOS Architecture Constitution 1.0

> **Version 1.0 — 2026-08-15 · Trạng thái: FROZEN**
> Toàn bộ Architecture Invariants **INV-001..INV-034** được freeze tại M10. **Vi phạm bất kỳ invariant nào = release blocker** (không còn warning).
> Enforcement: `backend/tests/test_architecture.py` (AST/import/literal tests) + `backend/src/aios_core/observability/arch_health.py` (scanner runtime) + ADR-0004.

## 15 Core Principle (thematic)

| # | Core Principle | Canonical INV |
|---|----------------|---------------|
| P1 | Runtime Isolation | INV-001 |
| P2 | Capability Isolation | INV-002 |
| P3 | Workflow Independence | INV-003 |
| P4 | Tool Independence | INV-004 |
| P5 | Control Plane Isolation | INV-005 |
| P6 | Contract First | INV-006 |
| P7 | Policy First | INV-007 |
| P8 | Artifact First | INV-008 |
| P9 | Event Driven | INV-009 |
| P10 | Deterministic First | INV-010 |
| P11 | Autonomous Action Boundary | INV-030 |
| P12 | Bounded Autonomy | INV-031 |
| P13 | Durable Execution | INV-032 |
| P14 | Evaluation Before Improvement | INV-033 |
| P15 | Validated Memory Promotion | INV-034 |

## Toàn bộ Invariants (INV-001..INV-034)

### M2 — Core (INV-001..010)

| ID | Tên | Nội dung | Enforce |
|----|-----|----------|---------|
| INV-001 | Runtime Isolation | Orchestrator không God Object; worker không chạm runtime service trực tiếp | arch tests `test_inv001_*` |
| INV-002 | Capability Isolation | Agent không chọn tool trực tiếp, chỉ chọn capability | arch tests `test_inv002_*` |
| INV-003 | Workflow Independence | Workflow không biết engine (compiler đổi không đổi definition) | arch tests `test_inv003_*` |
| INV-004 | Tool Independence | Workflow/agent không import tool implementation | arch tests `test_inv004_*` |
| INV-005 | Control Plane Isolation | Orchestrator không God Object, module hóa | arch tests `test_inv005_*` |
| INV-006 | Contract First | Component có contract version hóa | arch tests `test_inv006_*` |
| INV-007 | Policy First | Execution không bypass policy | arch tests `test_inv007_*` (hard call-site) |
| INV-008 | Artifact First | Kết quả quan trọng là artifact có metadata | arch tests `test_inv008_*` |
| INV-009 | Event Driven | Sự kiện qua event bus (4 business events) | arch tests `test_inv009_*` |
| INV-010 | Deterministic First | Rule engine/deterministic trước LLM | arch tests `test_inv010_*` |

### M5 — Core Intelligence (INV-011..016)

| ID | Tên | Nội dung | Enforce |
|----|-----|----------|---------|
| INV-011 | Memory Isolation | Agent không truy cập memory implementation trực tiếp | `test_inv011_*` |
| INV-012 | Context Budget | Context không vượt budget | `test_inv012_*` |
| INV-013 | Model Routing Policy | Model selection phải qua routing policy | `test_inv013_*` |
| INV-014 | Plan Validation | Execution Plan phải validate trước execution | `test_inv014_*` |
| INV-015 | Graph Acyclicity | Execution Graph không circular dependency | `test_inv015_*` |
| INV-016 | Scheduler Separation | Scheduler không sở hữu Resource/Execution | `test_inv016_*` |

### M6 — Harness (INV-017..021)

| ID | Tên | Nội dung | Enforce |
|----|-----|----------|---------|
| INV-017 | Harness Isolation | Harness chỉ qua Runtime/Orchestrator API, không chui vào implementation | `test_inv017_*` |
| INV-018 | Evidence First | Mọi Harness Run tạo evidence truy xuất được | `test_inv018_*` |
| INV-019 | Verification Before Verdict | Không PASS chỉ vì execution không exception | `test_inv019_*` |
| INV-020 | Evaluation Determinism | LLM Judge lưu model/prompt/temperature/input/output/score | `test_inv020_*` |
| INV-021 | Release Gate | Regression nghiêm trọng phải block release | `test_inv021_*` |

### M7 — Enterprise (INV-022..029)

| ID | Tên | Nội dung | Enforce |
|----|-----|----------|---------|
| INV-022 | Identity First | Mọi execution phải có Principal | `test_inv022_*` |
| INV-023 | Tenant Isolation | Cross-tenant access deny mặc định | `test_inv023_*` |
| INV-024 | Credential Isolation | Credential chỉ resolve trong authorized scope | `test_inv024_*` |
| INV-025 | Resource Fairness | Tenant không vượt quota nếu không có policy override | `test_inv025_*` |
| INV-026 | Distributed Execution Safety | Một execution chỉ một active lease | `test_inv026_*` |
| INV-027 | Audit Completeness | Security-sensitive action phải có audit evidence | `test_inv027_*` |
| INV-028 | Sandbox Boundary | Untrusted tool execution phải qua sandbox policy | `test_inv028_*` |
| INV-029 | Control Plane Isolation | Tenant workload không truy cập Control Plane nội bộ ngoài API contract | `test_inv029_*` |

### M9 — Autonomous (INV-030..034)

| ID | Tên | Nội dung | Enforce |
|----|-----|----------|---------|
| INV-030 | Autonomous Action Boundary | Mọi autonomous action phải qua Autonomy Governor | `test_m9_*` (governor gate) |
| INV-031 | Autonomy Bounded | Autonomous execution phải có budget/limit (step/cost/duration/risk) | `test_m9_*` (budget literals) |
| INV-032 | Long-running Resumable | Execution dài hạn phải checkpoint/resume được | `test_m9_*` (checkpoint/resume) |
| INV-033 | Self-Improvement via Harness | Cải thiện tự thân phải qua Experiment → Harness → Evaluation → Evidence → Decision | `test_m9_*` (evidence-first) |
| INV-034 | Autonomous Memory No Unverified Promote | Autonomous memory không tự promote thành Knowledge chưa kiểm chứng | `test_m9_*` (double gate) |

## Tuyên bố freeze

1. **INV-001..INV-034 là bất biến của AIOS 1.0** — vi phạm = release blocker (Gate A).
2. Sau M10: KHÔNG thêm invariant mới; thay đổi invariant hiện có phải qua ADR + đánh giá ảnh hưởng toàn bộ enforcement tests.
3. **Renumber 34 → 15 ID sạch là breaking change → deferred AIOS 2.0** (PLAN §M10-5).
4. Thay đổi fundamental architecture (Runtime contract / Agent model / Capability model / Plugin API) → **AIOS 2.0**.

## Hệ quả quy trình

- **Release Gate A**: `aiagent conformance` / CI chạy `backend/tests/test_architecture.py` + `aiagent arch-health` — `INV violations = 0` mới được release.
- **ADR bắt buộc**: mọi thay đổi liên quan invariant/constitution phải có `docs/adr/` entry.
- **Tài liệu chuẩn**: `docs/architecture-v2.md` + `docs/architecture/*` (bộ 1.0) — cập nhật khi milestone thay đổi kiến trúc.

## Lịch sử

| Version | Ngày | Nội dung |
|---------|------|----------|
| 1.0 | 2026-08-15 | Freeze INV-001..034 (M2: 001–010, M5: 011–016, M6: 017–021, M7: 022–029, M9: 030–034); 15 core principle; release blocker policy |
