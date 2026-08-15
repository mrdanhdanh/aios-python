# TASK-038 — Critique v1

## Vấn đề
- **P1-01**: LeaseManager & scheduler phải share clock để `is_expired` & `acquire` nhất quán. Test cũ dùng 2 clock khác nhau → false negative.
- **P2-01**: failover cần snapshot dict injectable.

## Resolution
- ✅ share mutable clock dict `{"t": 1000.0}` giữa lm & scheduler.
- ✅ `resume_snapshot` injectable callable.
