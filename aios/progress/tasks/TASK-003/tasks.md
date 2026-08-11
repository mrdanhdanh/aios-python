# TASK-003 — Breakdown checklist

> Quy ước: `[x]` = đã làm XONG VÀ đã verify.

## D1 — Semver helper + Contracts
- [ ] D1.1 `semver.py` — parse_version + compare (precedence số học)
- [ ] D1.2 `contracts/base.py` — ContractVersion, ContractMetadata(AiOSMetadata, Contract), Contract ABC
- [ ] D1.3 `contracts/compatibility.py` — CompatibilityChecker (5-rule) + CompatibilityResult + check_upgrade
- [ ] D1.4 `contracts/artifact.py` — ArtifactType + ArtifactContract (kế thừa, validate())
- [ ] D1.5 `contracts/__init__.py` + tests: test_semver.py, test_contracts.py

## D2 — DI Container
- [ ] D2.1 `container.py` — Container, ContainerError, Scope, register/register_instance/resolve/resolve_all/has/clear
- [ ] D2.2 Constructor injection (registration thắng default, Optional, Union → lỗi, RLock, circular detect)
- [ ] D2.3 Lifecycle start()/stop() idempotent, instance không hook → bỏ qua
- [ ] D2.4 tests: test_container.py

## D3 — Event Bus
- [ ] D3.1 `kernel/events.py` — Event (+to_dict), EventType, EventBus (subscribe/publish/flush)
- [ ] D3.2 Async path: _pending lock-protected + done_callback (CancelledError trước) + daemon thread ngoài loop
- [ ] D3.3 tests: test_event_bus.py (sync, filter, error isolation, async + flush, sync-thread, concurrent 2×50)

## D4 — Execution Plan
- [ ] D4.1 `kernel/execution_plan.py` — ExecutionPlan, PlanNode, PlanNodeType, status, Builder.from_dict, cycle detect
- [ ] D4.2 tests: test_execution_plan.py (6 case ValidationError + roundtrip equality)
- [ ] D4.3 `kernel/__init__.py` (export EventBus, Subscription, ExecutionPlan, ExecutionPlanBuilder, EventType) + **cập nhật `aios_core/__init__.py`** (export `contracts`, `Container`, `ContainerError`, `EventBus`, `ExecutionPlan`, `ExecutionPlanBuilder`) + test_import cập nhật (AC14)

## D5 — Verify + Commit
- [ ] D5.1 pytest: `backend/.venv/Scripts/python -m pytest` (cwd = `backend/`) → pass + coverage ≥ 80%; từ root smoke import pass
- [ ] D5.2 Commit (nhóm D1-D2, D3-D4, D5) — message tiền tố `M1-P0.5a: ...`
- [ ] D5.3 Ghi test.md + evaluation.md + cập nhật PROGRESS/LOG/STATS + commit cuối
