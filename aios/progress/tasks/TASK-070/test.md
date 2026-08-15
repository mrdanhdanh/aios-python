# TASK-070 — Test + Evaluation (Security Baseline 1.0)

## Test — `tests/test_security.py` **8/8 pass**
- 11 items đủ id (AC1)
- Deterministic (AC2) + evidence non-empty/specific (AC3)
- 4 critical checks (secrets/audit/sandbox/plugin_signing) PASS — cơ chế thật tồn tại
- blocking chỉ khi critical FAIL (AC4) + validation extra=forbid
- CLI security-check (AC5) — chạy thật: 9/11 pass, 2 warn (authentication/authorization), 0 fail → SECURE

## Full suite: **1891 passed** (AC6).

## Evaluation — 7/7 AC ĐẠT
| AC | Kết quả |
|----|---------|
| AC1 11 items | ✅ |
| AC2 deterministic | ✅ |
| AC3 evidence thật | ✅ |
| AC4 blocking | ✅ |
| AC5 CLI | ✅ |
| AC6 regression | ✅ |
| AC7 DoD | ✅ |

## Bài học
1. **Chống "check giả"**: mỗi check evidence = (module import + literal trong source + config flag) — test assert evidence chứa nội dung cụ thể.
2. WARN (authentication/authorization) phản ánh đúng thực tế: RBAC/ABAC tồn tại qua check_permission path nhưng authenticate flow chưa tách — ghi nhận làm việc tiếp theo.
3. Gate B input: critical FAIL = block — security-check là một phần của conformance (TASK-073).
