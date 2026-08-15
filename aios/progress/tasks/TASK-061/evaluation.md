# TASK-061 — Evaluation

## Đối chiếu AC
| AC | Kết quả |
|----|---------|
| 1. 7 signals | ✅ |
| 2. Repeated tool calls | ✅ |
| 3. Repeated errors | ✅ |
| 4. No state change | ✅ |
| 5. No progress | ✅ |
| 6. Oscillation | ✅ |
| 7. Budget burn | ✅ |
| 8. Contradictory plans | ✅ |
| 9. Verdict STUCK/NORMAL | ✅ |
| 10. Window injectable + coverage | ✅ |

## Bài học
- Oscillation detect O(n): states[i]==states[i+2] and states[i+1]==states[i+3]
- reset() khi replan/recovery thành công — đo lại từ đầu (tránh false positive kéo dài)

## Kết luận
**ĐẠT** — TASK-061 DONE.
