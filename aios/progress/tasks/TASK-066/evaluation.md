# TASK-066 — Evaluation

## Đối chiếu AC — 9/9 ĐẠT
Xem test.md. Điểm mấu chốt: resume KHÔNG chạy lại node done (đo bằng call count), journal corrupt → fail-closed, non-idempotent write → APPROVE/COMPENSATE (không tự retry).

## Bài học
1. **Exactly-once/at-least-once (PLAN §M10-14)**: read → retry; idempotent write → retry; non-idempotent → approval/compensation — đã hiện thực qua IdempotencyClassifier.
2. Journal + verify-before-resume là nền cho TASK-073 (Gate D Reliability) + TASK-066 gắn với INV-032.
3. Single-process assumption — distributed concurrent resume do M7 lease (INV-026) xử lý.

## Đề xuất (P3)
- Wire JournaledExecutor vào RuntimeKernel khi execution plan qua `--durable` (M10-P4 TASK-071).
