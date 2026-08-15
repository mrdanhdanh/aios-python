# TASK-066 — Tasks breakdown

- [ ] 1. Task folder + spec v2 (sau critique ×2)
- [ ] 2. Critique v1 (C1-01..04) + resolve; Critique v2 (C2-01..03) + resolve
- [ ] 3. tasks.md + review.md
- [ ] 4. Implement `kernel/durability.py`: ExecutionJournal (SQLite atomic, run_reason) + JournaledExecutor (node_runner + resume_point, verify trước resume, fail-closed) + IdempotencyClassifier (fail-closed default) + DurabilityPolicy
- [ ] 5. Config `DurabilitySettings` (enabled/db_path/policy) + config.yaml
- [ ] 6. Test `tests/test_durability.py`: journal trạng thái, crash-resume 4 node (count event), verify fail-closed, classifier 3 nhánh, non-idempotent retry chặn, policy rerun
- [ ] 7. Full suite regression
- [ ] 8. evaluation.md + implementation/README.md
- [ ] 9. DoD: LOG.md + PROGRESS.md + commit
