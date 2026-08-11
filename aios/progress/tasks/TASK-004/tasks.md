# TASK-004 — Breakdown checklist

> `[x]` = đã làm XONG VÀ đã verify.

## E1 — Config mở rộng + Context + Event
- [ ] E1.1 Mở rộng `Settings` (audit.db_path, artifacts.dir) + config.yaml + test_config
- [ ] E1.2 `services/context.py` — ContextScope, Context (frozen + _created_mono), ContextService (clock inject)
- [ ] E1.3 `services/events.py` — EventService (emit → audit SQLite + publish, query_audit -> list[Event])
- [ ] E1.4 tests: test_context.py, test_events.py

## E2 — Artifact + Permission + Policy
- [ ] E2.1 `services/artifacts.py` — ArtifactService (store/load/delete/list, sidecar, path guard, mkdir)
- [ ] E2.2 `services/permissions.py` — PermissionService (request/pending/grant/deny/on_ask)
- [ ] E2.3 `services/policy.py` — Policy + PolicyService (precedence deny>approval>allow)
- [ ] E2.4 `services/__init__.py` + `kernel/__init__.py` export + test_import cập nhật
- [ ] E2.5 tests: test_artifacts.py, test_permissions.py, test_policy.py

## E3 — Verify + Commit
- [ ] E3.1 pytest từ backend/ → pass, coverage ≥ 80%; git status sạch (AC11)
- [ ] E3.2 Commit code — message `M1-P0.5b: ...`
- [ ] E3.3 Ghi test.md + evaluation.md + cập nhật PROGRESS/LOG/STATS + commit cuối
