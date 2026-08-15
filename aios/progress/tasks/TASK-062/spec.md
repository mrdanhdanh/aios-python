# TASK-062 — Autonomous Scheduler (M9-P4)

## Mục tiêu
Từ `WHEN execute?` (SchedulerService M1 — queue kỹ thuật) thành **Autonomous Scheduler** chủ động (PLAN §M9-28): `Every night: inspect failed workflows → evaluate memory quality → detect stale skills → run regression → analyze arch health`. Proactive AIOS: User ↔ AIOS → System → Observation → Goal → AIOS acts; risk cao → Ask Human.

## Phạm vi
- `autonomous/scheduler.py`: `AutonomousScheduler` — trigger registry (interval/daily), run_due(now), last-run persist, target = callable (workflow/goal/observability task)
- `contracts.py`: `ScheduleTrigger` (id, kind: INTERVAL/DAILY, interval_s, at_hour, target_id, enabled), `TriggerRun` (trigger_id, at, result, status)

## Input/Output
- In: `register_trigger(trigger, fn)`; `run_due(now)`; Out: `list[TriggerRun]`
- Fail-closed: trigger target fn raise → ghi FAILED run (không crash scheduler)

## Tiêu chí chấp nhận (AC)
1. Trigger: INTERVAL (interval_s) + DAILY (at_hour 0-23) — `extra=forbid`
2. `run_due(now)`: chạy trigger đã đến hạn (last_run + interval ≤ now; DAILY: giờ khớp + chưa chạy hôm nay), trả TriggerRun list
3. Trigger disabled → không chạy
4. Last-run persist (SQLite) — restart không chạy lại trigger vừa chạy
5. Target fn raise → TriggerRun FAILED (không crash); result ghi note
6. Deterministic: cùng now → cùng trigger set
7. `run_due` emit event `autonomy.schedule` mỗi trigger chạy
8. Trigger validation: interval_s > 0 (INTERVAL), at_hour 0-23 (DAILY); trùng id → raise
9. Overdue handling: trigger quá hạn nhiều chu kỳ → chạy 1 lần (không bù n lần)
10. Contract `extra=forbid` + unit tests coverage ≥ 90%

## Amend (critique ×2 resolve)
- C1-01: `now: float` epoch; DAILY: `datetime.fromtimestamp(now).hour == at_hour` AND last_run_day < today; INTERVAL: last_run + interval_s ≤ now
- C1-02: day = int(now // 86400); sau khi chạy: last_day = today
- C1-03: bảng `autonomous_triggers` (persist metadata) + `autonomous_trigger_runs` (history bounded 1000)
- C1-04: fn registry in-memory {trigger_id: callable} — sau restart phải re-register (wiring)
- C1-05: trùng id → raise ScheduleError (fail-fast)
- C2-01: run_due không trigger → trả []
- C2-02: mỗi trigger chạy tối đa 1 lần/run_due
- C2-03: event {trigger_id, kind, status, at}
