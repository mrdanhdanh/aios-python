# TASK-049 — M8-E7 Certification — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `ecosystem/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/ecosystem/certification.py` — `CertLevel` 4 (COMMUNITY/VERIFIED/CERTIFIED/ENTERPRISE_CERTIFIED) + `certify()` 6 check groups (Contract/Security/Permission/Compatibility/Harness/Performance) + evidence + security hard-block
- `backend/src/aios_core/ecosystem/contracts.py` — certification evidence contracts
- `backend/src/aios_core/ecosystem/errors.py`

## Key behavior
- Plugin states: COMMUNITY → VERIFIED → CERTIFIED → ENTERPRISE CERTIFIED
- Mọi check fail → level COMMUNITY + report FAIL; VERIFIED khi basic checks pass; CERTIFIED khi threshold + security pass; ENTERPRISE_CERTIFIED khi enterprise evidence pass
- `check_fn` injectable — Harness gate (M6) là gate của Ecosystem; security fail → hard-block (không đạt dù các check khác pass)
- Harness (M6) không tồn tại độc lập: Plugin → Harness {Contract, Behavior, Security, Policy, Regression, Performance, Compatibility} → fail → CERTIFICATION = FAIL

## Verification
- `pytest` full suite: **1639 passed** — xem `test.md` + `tests/test_ecosystem_certification.py`
