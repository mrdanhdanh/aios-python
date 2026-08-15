# TASK-049 — Test + Evaluation

## Test
`tests/test_ecosystem_certification.py` (9 tests): levels, full pass → ENTERPRISE_CERTIFIED, missing permissions block, wildcard security hard-block, certified (no publisher), bad version, injectable check, threshold validation, deterministic + no mutation.

## Evaluation
Đạt 8/8 AC. 6 check groups (contract/behavior/security/permission/compatibility/performance) — behavior/performance placeholder pass-with-note; security fail hard-blocks CERTIFIED+; evidence bắt buộc; engine pure orchestrate (checks injectable). Fix: `checks=[]` không được rơi vào default (`is None` check).
**TASK-049 DONE**
