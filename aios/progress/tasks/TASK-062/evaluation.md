# TASK-062 — Evaluation

## Đối chiếu AC
| AC | Kết quả |
|----|---------|
| 1. Trigger INTERVAL/DAILY | ✅ |
| 2. run_due(now) deterministic | ✅ |
| 3. Disabled skip | ✅ |
| 4. Last-run persist restart | ✅ |
| 5. fn raise → FAILED (không crash) | ✅ |
| 6. Deterministic cùng now | ✅ |
| 7. Event autonomy.schedule | ✅ (code) |
| 8. Validate + trùng id raise | ✅ |
| 9. Overdue 1 lần | ✅ |
| 10. extra=forbid + coverage | ✅ |

## Bài học
- fn registry in-memory — restart phải re-register (wiring) — metadata persist đủ để biết trigger nào thiếu fn
- day = int(now // 86400) so sánh ngày DAILY không phụ thuộc timezone phức tạp

## Kết luận
**ĐẠT** — TASK-062 DONE.
