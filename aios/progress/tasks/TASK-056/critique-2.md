# TASK-056 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — Resume có validate checkpoint không?
→ **Resolve**: resume chỉ trả checkpoint khi session ACTIVE/RESUMED; COMPLETED/FAILED → raise LongHorizonError (không resume terminal).

## C2-02 (P2) — `current` bắt buộc?
→ **Resolve**: checkpoint đầu tiên có thể chưa có current (chưa bắt đầu) — current default ""; completed+pending phải nhất quán (không overlap).

## C2-03 (P3) — Session goals liên kết?
→ **Resolve**: `goal_id` field trong session (không FK cứng — autonomous goal engine có thể chưa tồn tại row).

## Kết luận
Resolve xong — spec đủ chặt.
