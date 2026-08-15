# TASK-066 — Test + Evaluation (Durable Execution 1.0)

## Test — `tests/test_durability.py` **10/10 pass**
- Journal persist trạng thái + nodes_done (AC1)
- Crash giữa node → resume: node done KHÔNG chạy lại (AC2 — event/call count)
- Resume thiếu journal / verify lệch → JournalError fail-closed (AC3)
- IdempotencyClassifier 3 nhánh + non-idempotent không bao giờ RETRY (AC4/AC5)
- DurabilityPolicy rerun (AC6) + config (AC7)

## Full suite: **1855 passed** — không phá M1–M9 (AC8).

## Evaluation — 9/9 AC ĐẠT
| AC | Kết quả |
|----|---------|
| AC1 journal trạng thái node | ✅ |
| AC2 resume không chạy lại node done | ✅ |
| AC3 fail-closed | ✅ |
| AC4 classifier 3 nhánh | ✅ |
| AC5 chặn tự retry non-idempotent | ✅ |
| AC6 policy rerun | ✅ |
| AC7 config | ✅ |
| AC8 regression | ✅ |
| AC9 DoD | ✅ |

## Bài học
1. ExecutionService hiện đã có snapshot/resume — journal là lớp tăng cường opt-in qua node_runner (không đụng internals).
2. Resume = verify (journal ↔ snapshot) TRƯỚC khi chạy tiếp — fail-closed quan trọng cho autonomous (INV-032).
3. run_reason (first_run/resume/rerun_by_policy) ghi audit — cần cho Gate D/E.
