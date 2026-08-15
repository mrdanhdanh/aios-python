# TASK-052 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — `observed_at` format + clock: timezone?
→ **Resolve**: `observed_at: float` (epoch seconds từ clock injectable — deterministic test); `snapshot()` xuất ISO string cho hiển thị.

## C2-02 (P2) — effective_confidence lưu hay tính?
Lưu effective_confidence vào history hay tính lúc get?
→ **Resolve**: lưu raw (confidence, observed_at); `get_fact` trả `WorldFact` + field tính `effective_confidence` (freshness tại thời điểm get). History lưu raw.

## C2-03 (P3) — `WorldState.constraints` kiểu gì?
→ **Resolve**: `dict[str, Any]` (flat — từ goal.constraints + policy constraints observed).

## Kết luận
Resolve xong — spec đủ chặt để implement.
