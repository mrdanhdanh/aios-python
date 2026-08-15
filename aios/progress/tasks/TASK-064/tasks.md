# TASK-064 — Tasks breakdown

- [ ] 1. Tạo task folder + spec.md (v2 sau critique ×2)
- [ ] 2. Critique vòng 1 (C1-01..05) + resolve → spec v2
- [ ] 3. Critique vòng 2 (C2-01..03) + resolve
- [ ] 4. tasks.md + review.md
- [ ] 5. Implement `contracts/catalog.py`: ContractLifecycle + ContractDefinition (extra=forbid, deprecated_in/reason bắt buộc khi DEPRECATED) + ContractCatalog (10 contract, schema_ref import thật, source_version)
- [ ] 6. Implement `contracts/check.py`: ContractChecker — check_all() matrix (✓/⚠/✗ + blocking + breaking_count + warning_count) + check_deprecated_usage(used)
- [ ] 7. CLI: `aiagent contract-check` + `aiagent contract list` (workflow/cli.py, additive)
- [ ] 8. Test `tests/test_contracts_catalog.py`: đủ 10 contract, 7 trường, import thật, lifecycle validation fail-closed, matrix kịch bản, deprecated usage, CLI chạy thật
- [ ] 9. Full suite regression (pytest backend)
- [ ] 10. evaluation.md + implementation/README.md
- [ ] 11. DoD: LOG.md + PROGRESS.md + commit
