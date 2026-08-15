# TASK-068 — M10-F4: Kill Switch (emergency stop)

## Mục tiêu
PLAN §M10-18: `aiagent stop execution <id>` · `aiagent stop goal <id>` · `aiagent emergency-stop` — Autonomous loops STOP · New tasks STOP · New tool calls BLOCK · Pending approvals CANCEL · Running reversible ROLLBACK.

## Phạm vi
- `kernel/kill_switch.py`:
  - `KillSwitch`: `stop_execution(execution_id)` (gọi ExecutionService.cancel), `stop_goal(goal_id)` (cascade cancel qua GoalManager), `emergency_stop()` (set state EMERGENCY: chặn execution mới + tool calls mới + autonomous loop mới; cancel approvals pending; đánh dấu reversible rollback)
  - `EmergencyState` (singleton in-memory + event `emergency.stopped`): `is_emergency()`, `block_new_work()`, `block_tool_call()`, counters
  - `ExecutionGate`: hook để ExecutionService/tool guard check emergency trước khi chạy (đăng ký vào RuntimeKernel — không sửa ExecutionService internals, gate qua `preflight()`)
- CLI: `aiagent stop execution <id>` / `aiagent stop goal <id>` / `aiagent emergency-stop` / `aiagent status` (emergency flag)
- Wiring: RuntimeKernel.create register KillSwitch

## Ngoài phạm vi
- Không sửa ExecutionService/GoalManager (gọi qua public API cancel)
- Không rollback tự động dữ liệu (chỉ đánh dấu; rollback thực thi ở M10-P5 migration)

## Input
- `kernel/services/execution.py` (cancel), `orchestrator/goals/goal.py` (GoalManager cascade cancel), `kernel/events.py` (EventType)

## Output
- `backend/src/aios_core/kernel/kill_switch.py` + CLI + `tests/test_kill_switch.py`

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | `stop_execution(id)` → ExecutionService cancel (execution CANCELLED/không chạy tiếp) | Test với ExecutionService thật |
| AC2 | `stop_goal(id)` → goal chuyển CANCELLED + tasks cascade | Test GoalManager thật |
| AC3 | `emergency_stop()`: state EMERGENCY + event phát | Test |
| AC4 | Sau emergency: execution mới bị chặn (preflight fail) | Test |
| AC5 | Sau emergency: tool call mới bị chặn (gate block) | Test |
| AC6 | Sau emergency: `release()` → hết emergency, hệ thống hoạt động lại | Test |
| AC7 | `emergency_stop()` gọi 2 lần idempotent (không double event/state lỗi) | Test |
| AC8 | CLI `stop execution/goal` + `emergency-stop` + `status` chạy thật | Test CLI |
| AC9 | Regression full suite | pytest |
| AC10 | Đóng DoD | checklist |

## Ghi chú
- Emergency = kill-switch bypass = 0 (Gate E) — KillSwitch là gate duy nhất, không shortcut.
- Rollback reversible: emergency_stop đánh dấu executions đang chạy có trạng thái `reversible` để M10-P5 xử lý.
