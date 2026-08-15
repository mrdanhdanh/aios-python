# TASK-062 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Clock: run_due(now) với now float hay datetime?
→ **Resolve**: `now: float` epoch seconds (deterministic test); DAILY so giờ: `datetime.fromtimestamp(now).hour == at_hour` + chưa chạy hôm nay (track theo `last_run_day`). INTERVAL: `last_run + interval_s ≤ now`.

## C1-02 (P2) — "Chưa chạy hôm nay" xác định thế nào?
→ **Resolve**: lưu `last_run_at` (epoch) + tính day = int(now // 86400); trigger DAILY chạy khi hour khớp AND last_day < today. Sau khi chạy: last_day = today.

## C1-03 (P2) — Persist schema?
→ **Resolve**: bảng `autonomous_triggers` (id, kind, interval_s, at_hour, target_id, enabled, last_run_at, last_run_day) — triggers persist qua restart; run history `autonomous_trigger_runs` (id, trigger_id, at, status, note) bounded 1000.

## C1-04 (P3) — Trigger target fn lưu ở đâu?
→ **Resolve**: fn registry in-memory `{trigger_id: callable}` — persist chỉ metadata; sau restart phải re-register (wiring làm).

## C1-05 (P3) — Trùng id trigger → raise hay skip?
→ **Resolve**: raise `ScheduleError` (fail-fast — config lỗi).

## Kết luận
Resolve xong. Vòng 2 kiểm tra.
