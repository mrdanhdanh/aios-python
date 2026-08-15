# TASK-070 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P2) — SecurityReport blocking nên tách critical/high
→ **Resolve**: SecurityItem có `severity: critical|high|medium`; blocking = có FAIL severity critical. Báo cáo đếm theo severity.

### C2-02 (P3) — Recommendation mỗi item
→ **Resolve**: SecurityItem.recommendation bắt buộc non-empty (mọi FAIL/WARN đều có hướng khắc phục).

### C2-03 (P3) — WARN ngữ nghĩa
→ **Resolve**: WARN = cơ chế tồn tại nhưng flag tắt (vd sandbox policy không enforce) — ghi rõ trong evidence.

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
