# TASK-069 — Tasks breakdown

- [ ] 1. Task folder + spec v2
- [ ] 2. Critique v1 + v2 + resolve
- [ ] 3. tasks.md + review.md
- [ ] 4. Implement `observability/slo.py`: SloKind (RATIO/ABSOLUTE_ZERO) + SloDefinition (extra=forbid, target 0..1) + SloRegistry (7 ratio + 5 zero-gate) + SloEngine.check(metrics) → SloReport (PASS/FAIL/SKIPPED, release_ready) + report_for_runtime(kernel)
- [ ] 5. CLI `aiagent slo` (bảng + verdict)
- [ ] 6. Test `tests/test_slo.py`: 12 SLO, biên RATIO, ABSOLUTE_ZERO 1 lần fail, release_ready với SKIPPED, report_for_runtime DB rỗng, CLI thật
- [ ] 7. Full suite regression
- [ ] 8. evaluation.md + implementation/README.md
- [ ] 9. DoD: LOG.md + PROGRESS.md + commit
