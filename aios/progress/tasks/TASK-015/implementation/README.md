# TASK-015 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Skill base (10 `SkillState` + transitions T1-T10) | `backend/src/aios_core/skills/base.py` |
| Skill Manager (lifecycle + optimistic concurrency) | `backend/src/aios_core/skills/manager.py` |
| Skill Registry (read-through) | `backend/src/aios_core/skills/registry.py` |
| Skill Sources (Zip/Git/Pip stub, no-syscall) | `backend/src/aios_core/skills/sources.py` |
| Skill schema / errors | `backend/src/aios_core/skills/schema.py`, `errors.py` |
| Sandbox Pool (warm reuse + evict) | `backend/src/aios_core/sandbox/pool.py`, `errors.py` |
| Tests | `test_skills_base.py`, `test_skills_manager.py`, `test_sandbox_pool.py` |

## Quyết định kỹ thuật (qua critique ×2 + review)
- Skill state machine enforced qua `assert_transition` + optimistic `WHERE state=<old>`
  (distinguish not-found vs concurrent change).
- Sandbox: `acquire` tái dùng container idle (warm=True), `evict_idle(now=)` dùng monotonic
  clock, không background thread.
