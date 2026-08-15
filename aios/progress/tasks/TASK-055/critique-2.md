# TASK-055 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — Circuit breaker mở thì recover() làm gì?
→ **Resolve**: recover() check breaker trước: fingerprint đang OPEN → trả outcome escalated sớm (reason "circuit open") — không chạy strategies.

## C2-02 (P2) — Đếm fail cho breaker ở đâu?
→ **Resolve**: mỗi recover() thất bại (execute fail hoặc verify fail) → `record_failure(fingerprint)` tăng count; thành công → reset count (CLOSED).

## C2-03 (P3) — Cooldown xử lý?
→ **Resolve**: sau khi OPEN, `cooldown_until = now + cooldown_s`; recover() gọi trước cooldown_until → escalated sớm; hết cooldown → reset về CLOSED (thử lại lần đầu).

## Kết luận
Resolve xong — spec đủ chặt.
