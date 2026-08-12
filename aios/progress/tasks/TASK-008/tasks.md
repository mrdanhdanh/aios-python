# TASK-008 — Breakdown checklist

## I1 — DAG helper + Definition
- [ ] I1.1 `kernel/dag.py` — validate_dag (3 check, message giữ nguyên) + ExecutionPlan validator refactor
- [ ] I1.2 `workflow/definition.py` — WorkflowDefinition + WorkflowNode (extra forbid, 9 validators, edges property, from_dict/from_yaml)
- [ ] I1.3 test_definition.py (9 case + edges + roundtrip) + chạy 107 test TASK-003 không sửa

## I2 — Compiler + Library + CLI
- [ ] I2.1 `workflow/compiler.py` — WorkflowCompiler ABC + MockCompiler (merge None-vs-0, READY) + LangGraphCompiler stub
- [ ] I2.2 `workflow/library.py` — WorkflowLibrary (register(definition), search, promote, thread-safe)
- [ ] I2.3 `workflow/cli.py` + errors.py + __init__ exports + aios_core/__init__ re-export
- [ ] I2.4 test_compiler.py (merge 4 case, plan mapping, stub), test_library.py (7 case), test_cli.py (main + simulate required) + **cập nhật test_import.py + test_exports_present**

## I3 — Verify + Commit
- [ ] I3.1 pytest pass (kể cả 107 TASK-003), coverage ≥ 80%, git sạch
- [ ] I3.2 Commit code + progress files + commit cuối
