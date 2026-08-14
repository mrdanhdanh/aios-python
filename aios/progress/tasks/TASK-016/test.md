# TASK-016 — Test Results

- **Test command:** `backend/.venv/Scripts/python -m pytest` (full suite, includes arch scan)
- **Result at closeout:** **502 passed + 2 skipped → 10/10 AC** (arch tests active after
  TASK-013/014/015 added `agents/`/`tools/`/`skills/`/`sandbox/`)
- **New test files:** `test_architecture.py` (AST pure scan, no runtime import),
  `_arch_scan.py` (helper)
- **Key AC verified (traceability — INV-001..010):**
  - INV-001 Worker Runtime Isolation → `test_inv001_worker_no_runtime` (active)
  - INV-002 Capability/No-direct-Tool → `test_inv002_worker_no_direct_tool` (active)
  - INV-003 Workflow Independence → `test_inv003_workflow_no_engine`
  - INV-004 Capability Independence → `test_inv004_capability_no_tool_impl`
  - INV-005 Control Plane Isolation (rule A + rule B planner allow-list) →
    `test_inv005_rule_a_no_business_models`, `test_inv005_rule_b_planner_allowlist`
  - INV-006 Contract purity → `test_inv006_contracts_purity`
  - INV-007 Policy First (hard call-site) → `test_inv007_policy_first_hard`
  - INV-009 Event Driven (4/8 business) → `test_inv009_event_driven_partial`
  - INV-010 Deterministic First → `test_inv010_deterministic_first`
  - Allow-list tests: agents/tools/skills/sandbox imports → `test_inv_*_import_allowlist`
- **Fail-closed:** scanner reports mọi file quét được; syntax/import lỗi → test FAIL (không silent-skip).
