# TASK-059 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — Agent chọn thế nào khi nhiều agent đủ capability?
→ **Resolve**: nhận `agents: list[dict]` (id, capabilities) — chọn agent đầu tiên (sorted theo id) có đủ capability — deterministic. Không cần AgentSelector M2 (đã có — đây là v1 delegation).

## C2-02 (P2) — Deadline/budget có enforce không?
→ **Resolve**: v1 lưu (contract) — enforce để wiring/governor. Ghi chú.

## C2-03 (P3) — Kết quả FAILED task — có dừng chuỗi không?
→ **Resolve**: SEQUENTIAL: task fail → các task sau đánh dấu SKIPPED (fail-fast chain); kết quả trả đủ với status.

## Kết luận
Resolve xong — spec đủ chặt.
