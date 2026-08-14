# TASK-014 — Test Results

- **Test command:** `backend/.venv/Scripts/python -m pytest` (full suite)
- **Result at closeout:** **622 passed, 0 skipped, coverage 96.15%, 14/14 AC**
  (baseline TASK-013 = 549; TASK-014 added 73 tests)
- **New test files:** `test_tools_base.py`, `test_tool_stubs.py`, `test_tool_registry.py`
- **Key AC verified (traceability — INV-002/security):**
  - Tool allow-list cứng (chỉ metadata + pydantic + stdlib + urllib.parse) →
    `test_inv_tools_import_allowlist` (active).
  - Tool `run` template 1-6: tool_id → gate fail-closed (None/False/raise) → started →
    `_run` → finished (even on error) → `test_tools_base.py`.
  - 6 stub tools (Python `ast.parse` no-exec / Docker mock / REST validate / MCP registry stub /
    Shell no-exec scope bắt buộc / Git mock) → `test_tool_stubs.py`.
  - Tool Registry `bind_capabilities` (idempotent, callable injectable) +
    capability swap (`execute_code: docker→mock` không đổi tool contract) → `test_tool_registry.py`.
