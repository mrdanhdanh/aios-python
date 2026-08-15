# TASK-065 — Tasks breakdown

- [ ] 1. Task folder + spec v2 (sau critique ×2)
- [ ] 2. Critique v1 (C1-01..04) + resolve; Critique v2 (C2-01..03) + resolve
- [ ] 3. tasks.md + review.md
- [ ] 4. Implement `kernel/hardening.py`: FailureKind (12) + FailureScenario (fault/detect/contain/recover/resume hooks) + FailureMatrix (registry, trùng id → raise) + HardeningRunner.run_all() → ScenarioOutcome list
- [ ] 5. Implement 12 scenario thật (ít nhất 8 end-to-end): model/tool/agent/process/network/db/plugin/worker_timeout/resource/memory_corruption/checkpoint/event_consumer
- [ ] 6. Test `tests/test_hardening.py`: đủ 12 kind, 8+ end-to-end, runner không crash, outcome fields, validation, regression
- [ ] 7. Full suite regression
- [ ] 8. evaluation.md + implementation/README.md
- [ ] 9. DoD: LOG.md + PROGRESS.md + commit
