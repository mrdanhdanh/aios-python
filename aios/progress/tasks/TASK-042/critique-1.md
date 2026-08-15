# TASK-042 — Critique v1

## Vấn đề
- **P2-01**: dashboard phải inject audit store (không import trực tiếp) để test offline.
- **P3-01**: success_rate chia cho 0 → guard.

## Resolution
- ✅ constructor nhận `audit_store`.
- ✅ guard division by zero.
