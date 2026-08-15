# TASK-065 — Evaluation

## Đối chiếu AC — 8/8 ĐẠT

| AC | Tiêu chí | Kết quả |
|----|----------|---------|
| AC1 | 12 FailureKind đúng PLAN §M10-12 | ✅ |
| AC2 | detect → contain → recover → resume mỗi scenario | ✅ (12/12 scenario) |
| AC3 | ≥8/12 end-to-end trên RuntimeKernel/component thật | ✅ 12/12 |
| AC4 | runner không crash cả suite | ✅ |
| AC5 | outcome ghi detect/contain/recovered/resumed | ✅ |
| AC6 | không sửa 9 services (1855 full suite pass) | ✅ |
| AC7 | validation deterministic | ✅ |
| AC8 | DoD | ✅ |

## Bài học
1. **Fail-closed API chi phối cách viết failure test**: Tool.run bắt exception → detect qua `output.ok`; ExecutionService chạy runner trong thread (timeout>0) → exception bị đóng hộp; Assistant.handle không raise → detect qua `status=="error"`.
2. **SQLite tự tạo file mới khi connect** → "db mất" phải detect bằng thiếu bảng, không phải connect lỗi.
3. Giá trị của Failure Matrix: chứng minh mọi lỗi có đường recover/resume — nền cho Durable Execution (TASK-066) + Reliability SLO (TASK-069).

## Đề xuất (P3)
- Thêm Failure Matrix runner vào `aiagent doctor` (diagnostics hook) ở M10-P4 (TASK-071).
