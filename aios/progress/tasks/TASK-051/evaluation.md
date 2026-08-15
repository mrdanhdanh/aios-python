# TASK-051 — Evaluation

## Đối chiếu AC
| AC | Kết quả |
|----|---------|
| 1. AutonomyPlan đủ assumptions/steps/success_conditions/rollback | ✅ |
| 2. Step: id/description/capability/dependencies | ✅ |
| 3. Deterministic (sorted) | ✅ |
| 4. success_conditions từ goal.success | ✅ |
| 5. rollback.enabled=False khi delete | ✅ |
| 6. replan + reasons | ✅ |
| 7. over_budget phản ánh max_duration | ✅ (amend C1-05: không raise) |
| 8. Validation objective/capabilities rỗng raise | ✅ |
| 9. extra=forbid | ✅ |
| 10. Coverage | ✅ |

## Bài học
- Fail-closed capabilities rỗng đúng triết lý AIOS (mọi hành động qua capability)
- Risk table dùng chung constants (planner + governor) — một nguồn sự thật

## Kết luận
**ĐẠT** — TASK-051 DONE.
