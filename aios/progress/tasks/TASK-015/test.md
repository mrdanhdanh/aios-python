# TASK-015 — Test Results

- **Test command:** `backend/.venv/Scripts/python -m pytest` (full suite)
- **Result at closeout:** **669 passed, 0 skipped, coverage 95.51%, 18/18 AC**
  (baseline TASK-014 = 622; TASK-015 added 47 tests)
- **New test files:** `test_skills_base.py`, `test_skills_manager.py`,
  `test_sandbox_pool.py` (+ 2 allow-list arch tests)
- **Key AC verified (traceability — V2/V3):**
  - Skill lifecycle 10 trạng thái (resolve/validate/install/enable/disable/unload/reload/
    upgrade/rollback/remove) + state machine transitions → `test_skills_base.py`,
    `test_skills_manager.py`.
  - SkillManager optimistic concurrency (`UPDATE ... WHERE state=<old>`) + dependent check
    on rollback/remove → `test_skills_manager.py`.
  - Sandbox Pool reuse (warm-start) + `release` + `evict_idle(now=)` + health, RLock,
    không thread nền → `test_sandbox_pool.py`.
