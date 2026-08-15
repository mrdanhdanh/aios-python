# TASK-066 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P1) — Resume sau crash phải verify "node done có snapshot thật"
Journal nói done nhưng state snapshot thiếu → resume chạy tiếp vẫn mất dữ liệu node đó.
→ **Resolve**: `verify(execution_id)`: mỗi node done phải có journal done + (nếu node sinh artifact/snapshot) snapshot tương ứng trong state; lệch → raise JournalError (fail-closed, không resume bừa).

### C2-02 (P2) — Policy rerun: ghi chú trong journal
Khi policy = rerun, execution chạy lại từ đầu — phải ghi rõ trong journal (run_reason) để audit.
→ **Resolve**: Journal có cột `run_reason` (first_run/resume/rerun_by_policy); resume ghi reason=resume.

### C2-03 (P3) — Concurrent resume
Hai tiến trình cùng resume 1 execution → double-run. (M7 lease đã giải quyết distributed; ở đây ghi chú).
→ **Resolve**: Ghi chú trong spec: single-process assumption; distributed dùng lease M7 (INV-026).

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
