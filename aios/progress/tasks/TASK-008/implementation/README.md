# TASK-008 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| DAG helper (refactor thuần) | `backend/src/aios_core/kernel/dag.py` + `execution_plan.py` (gọi helper) |
| Workflow definition | `workflow/definition.py` (WorkflowDefinition + WorkflowNode, extra forbid, edges property, from_dict/from_yaml) |
| Compilers | `workflow/compiler.py` (MockCompiler + LangGraphCompiler stub + get_compiler) |
| Library | `workflow/library.py` (canonical name, search, promote, thread-safe) |
| CLI | `workflow/cli.py` (`python -m ... run <yaml> --simulate` — deliverable M1) |
| Tests (4 file mới) | `test_definition.py`, `test_compiler.py`, `test_library.py`, `test_cli.py` |
| Fix bug ẩn | `contextlib.closing` ở events/conversation/vector/chunks/knowledge (16 chỗ) |

## Quyết định kỹ thuật (qua critique ×2 + review)
- **Canonical name = definition.name** (register không tham số name riêng); plan.id = `wf:{name}`
- **Merge None-vs-0**: node override > definition default > PlanNode default; `timeout_s=0` giữ 0 (engine: không timeout); `retries=0` giữ 0 (engine: 1 attempt)
- **dag.py**: duck-type, ValueError (pydantic wrap), thứ tự unique → unknown → cycle, message giữ nguyên
- **CLI**: `--simulate` bắt buộc v1; audit db trong TemporaryDirectory; lazy-import
- **Definition**: extra forbid, type = PlanNodeType (fail-fast), retries=0/timeout_s=300.0 defaults khớp PlanNode
