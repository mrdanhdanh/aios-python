# TASK-038 — E4 Distributed Scheduler + Lease (M7) — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `enterprise/`
> package (single source of truth), not duplicated here.

## Source of truth
- `backend/src/aios_core/enterprise/scheduler.py`
- `backend/src/aios_core/enterprise/contracts.py` (Lease)

## Key classes / functions
- `LeaseManager` — single-active-lease-per-execution (**INV-026 Distributed Execution Safety**); `acquire` raises `LeaseError` if an unexpired lease already exists; `renew`/`release`/`is_expired`/`active_node`
- `DistributedScheduler` — `enqueue`/`schedule`/`failover`; uses injectable `node_selector`, `run_on_node`, `resume_snapshot` (no god object, INV-016 style)

## Verification
- `pytest tests/test_enterprise.py` (scheduler tests) + `tests/test_architecture.py::test_inv026_distributed_lease_single_active`
- Architecture invariant: `enterprise/` only imports intra-package + pydantic/stdlib.
