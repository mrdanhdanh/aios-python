# Critique ×1 — TASK-021 (critic subagent, vòng 1)

> 2026-08-13 | critic phản biện spec v1 — 7 P1 + 11 P2 + 7 P3 → spec v2.

## P1 (7) → Resolution
- **P1-1**: WORKFLOW_FAILED/CANCELLED/MODEL_CALL_* KHÔNG ai emit (execution chỉ emit STARTED/COMPLETED/TOOL_*) — AC6 auto-record fail path bất khả thi → **Resolve**: thêm emit FAILED/CANCELLED vào execution.py (AC10 đổi tương ứng); MODEL_CALL_* bỏ khỏi scope.
- **P1-2**: workflow_id không có trong payload (chỉ execution_id + plan_id = "wf:<name>") → **Resolve**: workflow_id := plan_id (opaque).
- **P1-3**: trùng tên SystemDoctor (agents/system_doctor.py đang register) → **Resolve**: đổi tên class observability thành `HealthDoctor`.
- **P1-4**: AC9 allow-list thiếu imports của doctor.py (skills/catalog/prompts) → **Resolve**: diagnostics qua hooks từ wiring — observability/ không import skills/catalog/prompts.
- **P1-5**: arch_health duplicate engine với _arch_scan.py → **Resolve**: move _arch_scan.py vào src (observability/arch_scan.py) + shim ở tests — 1 engine.
- **P1-6**: fake module trong src phá test_architecture → **Resolve**: `scan(package_dir=...)` nhận tham số; test dùng tmp dir.
- **P1-7**: cột `name` không định nghĩa → **Resolve**: workflow → plan_id; tool → node_name.

## P2 (11) → Resolve: orphan STARTED (NULL duration), backfill (ghi giới hạn no-backfill), audit = source of truth, SQLite pattern chuẩn, CLI wiring hooks, ObservabilitySettings mới, evaluate() KeyError, forbidden targets subset chính xác, policy check AST, workflow count qua hook, bỏ api/semver khỏi allow-list.

## P3 (7) → Resolve: tool_failures từ ok=false, recent sort desc + summary keys, sort_keys, autoincrement, CLI empty → zeros, profiler double-start raise, average None.

## Trạng thái: RESOLVED 25/25 → spec v2
