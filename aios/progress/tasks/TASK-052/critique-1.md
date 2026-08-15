# TASK-052 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Freshness và confidence decay: công thức deterministic phải xác định
"Confidence decay theo freshness" — decay tuyến tính? theo ngày? cần công thức cụ thể để test chính xác.
→ **Resolve**: `freshness = max(0.0, 1.0 - age_s / TTL_S)` với TTL_S injectable (mặc định 86400 = 24h); `effective_confidence = confidence * freshness`. Deterministic, test được.

## C1-02 (P2) — History phình to
Mỗi observe append history — không giới hạn thì snapshot phình.
→ **Resolve**: history giới hạn `max_history` per scope (mặc định 100, injectable) — FIFO trim.

## C1-03 (P2) — Value type
`value` có thể là số, chuỗi, dict — WorldFact.value type gì?
→ **Resolve**: `value: Any` (pydantic) nhưng snapshot JSON-serializable (test đảm bảo). V1 chấp nhận primitive + dict/list.

## C1-04 (P3) — get_fact theo name: nếu nhiều scope cùng name?
VD: `system.status` và `runtime.status` — name trùng nhưng khác scope.
→ **Resolve**: key = `f"{scope.value}.{name}"` — get_fact nhận scope + name (hoặc key đầy đủ). Unambiguous.

## C1-05 (P3) — WorldState.constraints từ đâu?
Constraints là input của planner — WorldModel chỉ lưu, không sinh.
→ **Resolve**: ghi rõ: WorldModel là store thuần (observable state), constraints/goals được observe từ ngoài (engine/loop ghi vào). Không sinh dữ liệu.

## Kết luận
P1 xác định công thức; P2-P3 resolve. Vòng 2 kiểm tra.
