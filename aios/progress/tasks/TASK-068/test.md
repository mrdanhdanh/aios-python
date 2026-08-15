# TASK-068 — Test + Evaluation (Kill Switch)

## Test — `tests/test_kill_switch.py` **13/13 pass**
- stop_execution → CANCELLED (cancel-before-execute) (AC1)
- stop_goal → cascade cancel goal + tasks (AC2)
- emergency_stop state + event (AC3); idempotent 2 lần (AC7)
- preflight chặn execution mới (AC4); preflight_tool chặn tool (AC5)
- release phục hồi + no-op an toàn (AC6)
- EventType mới + wiring kernel (AC9-ish)

## Full suite: **1891 passed** (AC9).

## Evaluation — 10/10 AC ĐẠT
| AC | Kết quả |
|----|---------|
| AC1-AC7 | ✅ (xem test.md) |
| AC8 CLI stop/emergency-stop/status | ✅ |
| AC9 regression | ✅ |
| AC10 DoD | ✅ |

## Bài học
1. **Wiring lazy**: KillSwitch không được resolve ExecutionService lúc khởi tạo (phá test fake) — dùng lambda resolve khi gọi.
2. Emergency = gate duy nhất (preflight/preflight_tool) — ToolGuard TASK-067 gọi preflight_tool → không cơ chế song song.
3. CLI `emergency-stop` + `status` cho phép vận hành thủ công nhanh — Gate E (kill-switch bypass = 0).
