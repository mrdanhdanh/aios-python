# TASK-069 — Test + Evaluation (Reliability SLO)

## Test — `tests/test_slo.py` **12/12 pass**
- 12 SLO: 7 ratio + 5 absolute-zero (AC1)
- RATIO biên (AC2) + ngoài [0,1] fail
- ABSOLUTE_ZERO: 1 lần = FAIL (AC3 — không trung bình hóa)
- release_ready: 1 gate fail chặn; SKIPPED không chặn (AC4)
- metrics_from_runtime: DB rỗng không crash + có workflow (AC5)
- CLI `aiagent slo` + validation extra=forbid (AC6/AC7)

## Full suite: **1855 passed** (AC8).

## Evaluation — 9/9 AC ĐẠT
| AC | Kết quả |
|----|---------|
| AC1 12 SLO đủ | ✅ |
| AC2 RATIO biên | ✅ |
| AC3 zero-gate 1 lần fail | ✅ |
| AC4 release_ready + SKIPPED | ✅ |
| AC5 runtime thật không crash | ✅ |
| AC6 CLI | ✅ |
| AC7 validation | ✅ |
| AC8 regression | ✅ |
| AC9 DoD | ✅ |

## Bài học
1. **MetricsService không ghi ok cho workflow finish** (thiết kế M4) → bổ sung additive: COMPLETED=1, FAILED/CANCELLED=0 + `counts_by_outcome()` — nguồn cho execution_success.
2. Non-averaged gates đúng tinh thần PLAN: 1 policy bypass = FAIL dù mọi SLO khác 99% — `release_ready` phản ánh.
3. `aiagent slo` → verdict RELEASE READY/NOT READY — sẽ được TASK-073 dùng làm Gate D/E.

## Đề xuất (P3)
- Wire `slo.release_ready` vào release gate TASK-073 + dashboard Health tab.
