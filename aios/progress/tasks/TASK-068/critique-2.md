# TASK-068 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P2) — Tool call block: gate phải dùng chung với TASK-067 ToolGuard
Tránh 2 cơ chế chặn tool song song.
→ **Resolve**: KillSwitch.preflight_tool() là một hook; ToolGuard (TASK-067) gọi preflight_tool() như gate đầu tiên — hợp nhất tại call-site. Test: guard + kill switch chặn cùng.

### C2-02 (P3) — release() sau emergency cần an toàn
→ **Resolve**: release() reset state + event `emergency.released`; gọi release khi chưa emergency → no-op (không lỗi).

### C2-03 (P3) — Event types mới
→ **Resolve**: +`EMERGENCY_STOPPED = "emergency.stopped"` + `EMERGENCY_RELEASED = "emergency.released"` (EventType).

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
