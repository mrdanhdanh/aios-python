# TASK-072 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P2) — Vitest cho TSX cần mock fetch/ws
View mới gọi api.ts → test cần mock.
→ **Resolve**: Vitest test dùng data mẫu trực tiếp (component nhận props/loading state) + mock fetch cho Overview fetch. Theo pattern vitest hiện có (MockWebSocket stub M3).

### C2-02 (P3) — Timeline sort theo thời gian
→ **Resolve**: API sort steps theo (ts, seq) asc; test assert thứ tự.

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
