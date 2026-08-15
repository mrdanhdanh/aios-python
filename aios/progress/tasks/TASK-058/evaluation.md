# TASK-058 — Evaluation

## Đối chiếu AC
| AC | Kết quả |
|----|---------|
| 1. INV-033 evidence-first | ✅ arch + behavioral |
| 2. Hypothesis contract | ✅ |
| 3. run() pipeline sandbox→evaluate→compare | ✅ |
| 4. Evidence bắt buộc | ✅ |
| 5. Compare direction higher/lower | ✅ |
| 6. deploy chỉ khi ACCEPTED | ✅ |
| 7. Persist SQLite | ✅ |
| 8. Event autonomy.experiment | ✅ (code) |
| 9. extra=forbid | ✅ |
| 10. Coverage | ✅ |

## Bài học
- evaluate_fn BẮT BUỘC constructor (fail-fast) — không default reject (test được accept path)
- Deploy = canary flag (KHÔNG tự sửa production — human thực thi)

## Kết luận
**ĐẠT** — TASK-058 DONE.
