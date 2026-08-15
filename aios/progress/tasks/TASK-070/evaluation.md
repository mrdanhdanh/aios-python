# TASK-070 — Evaluation

## Đối chiếu AC — 7/7 ĐẠT (xem test.md)

## Giá trị
- Security baseline 1.0 = 11 items chuẩn (PLAN §M10-23) — kiểm tra định kỳ được, deterministic, không network.
- Evidence thật (import + source literal) — không check giả; WARN cho hướng phát triển.

## Bài học
1. Check phải đọc source (inspect.getsource) chứ không chỉ import — import thành công không chứng minh cơ chế.
2. Severity + blocking đúng Gate B (critical = 0).

## Đề xuất (P3)
- Authentication/Authorization WARN → làm flow authenticate rõ ràng cho Principal (M10 sau release / AIOS 1.1).
