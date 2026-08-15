# TASK-074 — Test + Evaluation (Upgrade & Migration 1.0)

## Test — `tests/test_migration.py` **13/13 pass**
- Plan validation: steps rỗng/from==to/semver/extra=forbid (AC1)
- Dry-run không side effect (counter = 0) (AC2)
- Apply: steps + journal completed (AC3); rollback ngược thứ tự (AC4)
- Fail giữa chừng → journal FAILED + auto-rollback step đã apply (AC5)
- Idempotent: completed → từ chối (C2-03)
- Formats: config/workflow/plugin v0→v1 deterministic + không mutate input (AC6)
- CLI migrate dry-run/apply (AC7 — journal flag cho test isolation)

## Full suite: **1939 passed** (AC8).

## Evaluation — 9/9 AC ĐẠT
| AC | Kết quả |
|----|---------|
| AC1-AC7 | ✅ (xem trên) |
| AC8 regression | ✅ |
| AC9 DoD | ✅ |

## Bài học
1. CLI journal DB mặc định gây test pollution (idempotent chặn lần chạy 2) → `--journal` flag.
2. Auto-rollback best-effort: step không rollback_fn → bỏ qua, không crash.
3. MigrationFormats deterministic + deep-copy input (không mutate).
