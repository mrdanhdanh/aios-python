# TASK-075 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-075.

## Các vấn đề

### C1-01 (P1) — Concurrency max đo từ đâu?
→ **Resolve**: Đếm qua metrics rows: running = started chưa finished tại mỗi thời điểm; max = max concurrent tại overlap — đơn giản: max over time của (started_count - finished_count). MetricsService.recent + durations đủ. Hoặc injectable concurrency_fn — mặc định đếm từ metrics table.

### C1-02 (P2) — Storage đo thế nào (không du)?
→ **Resolve**: Artifact dir size qua os.scandir đệ quy (pure python) — dir không tồn tại → 0. Memory: không đo RSS (offline) — ghi chú estimate = 0, có slot injectable.

### C1-03 (P2) — cost_per_goal cần goal → tasks mapping
→ **Resolve**: GoalManager tasks có workflow_name → cost_per_goal = sum cost của workflows thuộc goal; chưa có execution thật → 0.0 (hợp lệ).

### C1-04 (P3) — CLI output ổn định
→ **Resolve**: Bảng cột padding + `Cost/Success: N (skipped khi 0 success)`.

## Kết luận
Resolve vào spec v2.
