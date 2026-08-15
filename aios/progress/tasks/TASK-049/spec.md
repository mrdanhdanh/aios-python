# TASK-049 — Certification (M8-E7)

## Mục tiêu
Plugin states `COMMUNITY → VERIFIED → CERTIFIED → ENTERPRISE_CERTIFIED` với Harness làm gate: Contract / Behavior / Security / Permission / Compatibility / Performance checks. Fail check → `CERTIFICATION = FAIL`.

## Phạm vi
- `ecosystem/certification.py`: `CertLevel` enum, `CertCheck` (name, status, evidence), `CertReport`, `CertificationEngine.certify(manifest_dict, checks=None) -> CertReport`.
- Checks mặc định deterministic (contract schema, permission required, aios compat, provides hợp lệ, name/version hợp lệ) + check_fn injectable.
- Level tăng dần: VERIFIED yêu cầu 100% checks pass; CERTIFIED yêu cầu ≥ threshold (mặc định 1.0) + không security fail; ENTERPRISE_CERTIFIED yêu cầu thêm evidence enterprise.

## Input/Output
- Input: manifest dict; Output: CertReport (level, checks, passed, failed, evidence).

## Tiêu chí chấp nhận
1. CertLevel 4 giá trị đúng PLAN.
2. certify() chạy checks; mọi fail → level COMMUNITY + report FAIL.
3. VERIFIED khi toàn bộ basic checks pass.
4. CERTIFIED khi threshold đạt + security pass.
5. ENTERPRISE_CERTIFIED khi enterprise evidence pass.
6. check_fn injectable (test harness gate).
7. Import allow-list ecosystem.
8. Test: levels, threshold, fail → COMMUNITY, injectable.
