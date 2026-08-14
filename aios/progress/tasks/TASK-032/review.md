# Review — TASK-032 (spec v3 trước implement)

**Reviewer**: orchestrator tự review (đối chiếu code thật — ghi nhận)

## Đối chiếu code thật
- H1 runner/Harness pattern: H2/H3 chứng minh (persist trước raise, update_state merge) ✓
- `_HARNESS_ALLOWED_AIOS`: evaluation/ cần aios_core.harness (intra) + kernel.services.state + logging — ✓ KHÔNG MOD
- `_HARNESS_ALLOWED_EXTERNAL`: pydantic/typing/enum/re/datetime + yaml (đã có từ TASK-031) — ✓ không cần thêm
- INV-020e: cấm aios_core.models* — evaluators stub thuần ✓ (không import models)
- Trajectory: steps dict → TrajectoryStep.model_validate — pydantic chấp nhận dict ✓

## Vấn đề
- **R2-1 — `numeric_ge` expected có thể là string**: so float(output) >= float(expected) — cả 2 parse; fail → 0.0 ✓ (ghi rõ trong implement).
- **R2-2 — aggregate mean khi value None**: bỏ qua None khi tính mean (chỉ mean trên giá trị có) nhưng Score.value = None nếu TẤT CẢ items None → inconclusive. Chốt.
- **R3-1 — summary prefix theo status** ✓; **R3-2 — reproducible chỉ LLM_JUDGE** ✓; **R3-3 — thresholds validator >= 0** ✓.

## Kết luận
- [x] **APPROVED có điều kiện** — 0 R1; 2 R2 + 3 R3 — resolve trong implement.
