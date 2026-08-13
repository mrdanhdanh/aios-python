# Critique ×2 — TASK-021 (critic subagent, vòng 2)

> 2026-08-13 | critic phản biện spec v2 — 2 P1 + 4 P2 + 5 P3 → spec v3.

## P1 (2) → Resolution
- **P1-1**: SRC_ROOT = parents[2] / "src" SAI (file ở src/aios_core/observability/ → parents[2] = backend/src → backend/src/src) → **Resolve**: SRC_ROOT = `parents[2]` (không thêm /src).
- **P1-2**: AC5 scan(tmp_path) mâu thuẫn dir_imports (relative_to hardcode SRC_ROOT → ValueError) → **Resolve**: arch_health tự rglob + `collect_imports(module_rel, package_dir)` — KHÔNG dùng dir_imports.

## P2 (4) → Resolution
- **P2-1**: bỏ sót ~5 nhánh FAILED early-return (policy rejected, approval required, resource ×2, resume early) → emit ở MỌI nhánh FAILED (6 chỗ).
- **P2-2**: re-run/resume cùng execution_id làm UPDATE ghi đè hết row → UPDATE row mới nhất chưa finish (MAX(id) subquery); EvaluationStore evaluate() UPDATE row mới nhất.
- **P2-3**: evaluate() không có write path production → thêm POST /evaluations/{execution_id}/feedback.
- **P2-4**: CANCELLED semantics undefined → success=false; counts {success, failed, total} — failed = FAILED + CANCELLED.

## P3 (5) → Resolve: category thay type (finish type khác start), node_id IS NULL cho workflow, cancel trước execute không emit, logging pin (không dùng riêng + shim docstring), plan_id opaque.

## Trạng thái: RESOLVED 11/11 → spec v3
