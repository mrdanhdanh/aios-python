# TASK-086 — Tasks breakdown (checklist)

> Spec v3 (10 AC). Hard gate: spec ✅ + critique-1 (9/9) ✅ + critique-2 (6/6) ✅

## A. Fix parse-only AiosRange (C1-01 + C2-04)
- [ ] A1. `plugins/contracts.py` — `AiosRange` thêm `compatible: list[str] = Field(default_factory=list)` (parse-only; check min/max KHÔNG đổi)
- [ ] A2. Test `test_aios_range_compatible_field` (parse + round-trip giá trị + min/max không đổi)

## B. Module `upgrade/backward_compat.py`
- [ ] B1. `BackwardCheck` (id/kind/description/run — được phép raise) + `BackwardCheckResult` + `BackwardCompatibilityReport`
- [ ] B2. `BackwardCompatibilitySuite` (CHECKS 9 check 5 kind; `__init__(checks=None)` — C2-05; `run()` bắt exception → fail-closed)
- [ ] B3. 9 scenario: workflow-v0-parse · workflow-v0-run-simulate (redirect_stdout C2-02 + YAML temp pathlib+uuid C2-03 + audit db temp C2-06) · plugin-v0-load · plugin-v1-compatible-field · contract-v0-compat · contract-v0-catalog · extension-v0-matrix (2 chiều) · migrated-110-data (round-trip C2-04) · migrated-v0-formats (per-kind validator)
- [ ] B4. Fixture v0 chuẩn (spec §3.2)

## C. Allow-list + CLI
- [ ] C1. `tests/test_architecture.py` — `_UPGRADE_ALLOWED_AIOS` + 7 module: workflow.definition, workflow.compiler, workflow.cli, plugins.contracts, contracts.catalog, contracts.compatibility, extension.matrix (kèm comment — C2-01)
- [ ] C2. CLI `workflow/cli.py` — subparser `compat verify` + dispatch + `_compat_verify()` (JSON 1 dòng, exit 0/1)

## D. Tests `tests/test_backward_compat.py`
- [ ] D1. Unit: 9 check chạy OK; suite run → report.ok True, 9 passed
- [ ] D2. Fail-closed: Suite(checks=[raise_check, ...]) → ok False + các check khác vẫn chạy (C2-05)
- [ ] D3. CLI: `compat verify` exit 0 + JSON cấu trúc + stdout ngoài JSON rỗng (C2-02); `compat list/check` không phá
- [ ] D4. AiosRange fix: parse + round-trip + min/max behavior

## E. Verify & đóng task
- [ ] E1. Targeted: `pytest tests/test_backward_compat.py tests/test_plugins.py tests/test_architecture.py tests/test_cli.py` — PASS
- [ ] E2. Full suite — 0 regression baseline 2098 + test mới PASS
- [ ] E3. CLI thật `aiagent compat verify` → exit 0
- [ ] E4. `arch-health` 0 violations + `doctor` healthy
- [ ] E5. test.md + evaluation.md + implementation/README.md; LOG/PROGRESS; commit — KHÔNG push
