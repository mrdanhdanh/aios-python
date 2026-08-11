# TASK-003 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Semver helper | `backend/src/aios_core/semver.py` |
| Contracts (base, artifact, compatibility) | `backend/src/aios_core/contracts/` |
| DI Container | `backend/src/aios_core/container.py` |
| Event Bus | `backend/src/aios_core/kernel/events.py` |
| Execution Plan | `backend/src/aios_core/kernel/execution_plan.py` |
| Tests (5 file mới) | `backend/tests/test_semver.py`, `test_contracts.py`, `test_container.py`, `test_event_bus.py`, `test_execution_plan.py` |
| Exports cập nhật | `backend/src/aios_core/__init__.py`, `kernel/__init__.py` |

## Quyết định kỹ thuật (đã qua critique ×2 + review)

- **Semver**: `parse_version`/`compare` với precedence chuẩn semver (identifier số học: alpha.10 > alpha.2); reuse `SEMVER_RE` từ metadata (1 nguồn sự thật)
- **Compatibility**: 5-rule đối xứng; `check_upgrade(old, new).compatible = is_compatible(installed=new, required=old)` (đảo tham số); breaking = major thay đổi hoặc 0.x minor bump; invariant breaking ⇒ ¬compatible
- **Container**: RLock chống deadlock; registration thắng default; overwrite khi register trùng (cho mock); `object.__init__` skip; Union/không hint → ContainerError; has/clear cho test isolation
- **EventBus**: snapshot dưới lock; sync handler wrap try/except; async trong loop → task + _pending + done_callback (CancelledError trước); ngoài loop → daemon thread asyncio.run; flush() gather return_exceptions
- **ExecutionPlan**: pydantic extra=forbid; PlanNodeType enum; cycle detect model_validator (kể cả self); roundtrip qua to_dict/from_dict
- **pydantic v2 notes**: validator shadowing theo tên method; abstractmethods bị clear — ghi chú trong code
