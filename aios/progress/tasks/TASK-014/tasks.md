# TASK-014 — Tasks Breakdown (Tools 6 loại + Tool Registry)

> Ngày: 2026-08-13 | Spec: `spec.md` (approved — critique ×2 resolved 27 vấn đề: 17 + 10)

## Checklist

### T1 — test_architecture.py (trước khi tạo tools/)
- [ ] T1.1 Thêm `test_inv_tools_import_allowlist`: rglob tools/ + collect_imports → exclude aios_core.tools* → check 2 set (aios_mods ⊆ {aios_core.metadata}; external ⊆ {pydantic, urllib} ∪ stdlib) + **urllib module-con check (chỉ urllib.parse — C1-04)**; skip nếu TOOLS_DIR chưa tồn tại

### T2 — `tools/` package (Execution Plane — allow-list cứng)
- [ ] T2.1 `base.py`: ToolInput/ToolOutput/ToolContext (pydantic, extra=forbid) + Tool ABC — template run (1-6: tool_id check → gate check [None/False/raise fail-closed] → started → _run(input, context) bọc Exception → finished → output); required_scopes rỗng → ValueError (C1-06); _stub_usage helper; error paths usage={} duration_s=0.0 (C1-12); constructor thống nhất (C2-10); C2-09 sink fallback
- [ ] T2.2 `python_tool.py` — ast.parse (không exec), execute flag forward-compat, invalid argument convention (C2-05)
- [ ] T2.3 `docker_tool.py` — MOCK_IMAGES, 3 actions
- [ ] T2.4 `rest_tool.py` — urllib.parse validate URL (KHÔNG urllib.request), 6 methods
- [ ] T2.5 `mcp_tool.py` — MCP_SERVERS + validate init (C1-10, C2-08)
- [ ] T2.6 `shell_tool.py` — scope shell BẮT BUỘC, no-exec
- [ ] T2.7 `git_tool.py` — MOCK_REPO_STATE, 3 actions
- [ ] T2.8 `registry.py` — ToolRegistry (RLock; register/get/list/list_by_capability/tools_for_capability/all_available/capabilities/bind_capabilities — trả tổng cặp kể cả lần 2 C1-11; không rollback C2-06)
- [ ] T2.9 `__init__.py` — exports + build_default_tools (thứ tự cố định) + build_tool_registry; `aios_core/__init__.py` + test_import.py

### T3 — Test (3 file mới)
- [ ] T3.1 `test_tools_base.py` — contract, mismatch, _run raise, gate deny/none/raise (AC9), events (AC10), scope cross-check
- [ ] T3.2 `test_tool_stubs.py` — 6 tool stub tests + invalid argument mỗi tool (C2-05) + no-exec marker (C1-01) + **test_no_syscall_all_tools (C2-03)**
- [ ] T3.3 `test_tool_registry.py` — registry + concurrent (prefix riêng) + **test_tool_concurrent_runs_same_instance (C2-04)** + binding CapabilityRegistry thật (AC12) + factory/metadata (AC13) + determinism (AC14)

### T4 — Chạy + đánh giá
- [ ] T4.1 `pytest -q` toàn bộ pass (549 baseline + mới, 0 skip)
- [ ] T4.2 Coverage tools/ ≥ 80%
- [ ] T4.3 `evaluation.md` đối chiếu 14 AC
- [ ] T4.4 PROGRESS.md / LOG.md / STATS.md + commit
