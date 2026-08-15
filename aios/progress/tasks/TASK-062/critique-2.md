# TASK-062 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — run_due trả gì khi không trigger?
→ **Resolve**: trả [] (empty list) — không raise.

## C2-02 (P2) — Trigger chạy 2 lần trong cùng run_due (INTERVAL nhỏ)?
→ **Resolve**: trong 1 run_due, mỗi trigger chạy tối đa 1 lần (chạy xong cập nhật last_run ngay).

## C2-03 (P3) — Event payload?
→ **Resolve**: {trigger_id, kind, status, at} — đủ cho dashboard.

## Kết luận
Resolve xong — spec đủ chặt.
