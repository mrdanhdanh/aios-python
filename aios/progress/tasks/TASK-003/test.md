# Test — TASK-003

## Kết quả thực tế

| Hạng mục | Kết quả |
|----------|---------|
| Lệnh chạy | `backend/.venv/Scripts/python -m pytest` (cwd = backend/) |
| Kết quả | **107 passed** (TASK-002: 32 + TASK-003: 75 mới) |
| Coverage | **94.82%** trên `aios_core` (ngưỡng 80% — pass) |
| Từ repo root | `pytest backend/tests` → 107 passed + smoke import OK |

Test file mới (TASK-003):
- `test_semver.py` — 8 tests (parse, invalid, compare core, precedence pre-release số học)
- `test_contracts.py` — 21 tests (ContractVersion, is_compatible 8 case, check_upgrade 4 case + invariant, ArtifactContract valid/invalid/unicode/validate)
- `test_container.py` — 22 tests (scopes, injection 8 luật, lifecycle, overwrite, has/clear, thread-safe)
- `test_event_bus.py` — 14 tests (sync, filter, unsubscribe, error isolation, async + flush, sync-thread, concurrent 2×50, to_dict)
- `test_execution_plan.py` — 12 tests (build, 6 case ValidationError, roundtrip equality)

## Lỗi phát hiện khi implement + fix

1. **pydantic v2 replace validator cùng tên method**: `_validate_semver` trong `ContractMetadata` đè validator `version` kế thừa từ `AiOSMetadata` → version "1.0" không bị chặn → đổi tên method (`_validate_contract_semver`/`_validate_version_meta`)
2. **Container `object.__init__`**: class không định nghĩa `__init__` (kế thừa object) có `*args, **kwargs` → bị lỗi varargs → skip khi `init is object.__init__`
3. **EventBus không wrap sync handler**: handler lỗi crash publish → thêm try/except + log warning
4. **Test shallow copy**: `dict(VALID_DATA)` share list `nodes` → test đầu mutate làm hỏng test sau → deepcopy
5. **pydantic v2 clears `__abstractmethods__`**: ContractMetadata không enforce abstract lúc instantiate (hành vi đã biết) → ghi chú trong code, dùng `validate()` làm enforcement point

## Đối chiếu AC (20 AC)
**20/20 PASS** — chi tiết:
- AC1 ✅ ContractVersion semver 2 field + pre-release (test_contracts)
- AC2 ✅ 8 case is_compatible (test_contracts parametrize)
- AC3 ✅ ArtifactContract 8 case (test_contracts)
- AC4 ✅ TypeError/ContainerError (test_container)
- AC5 ✅ 3 scopes + register_instance (test_container)
- AC6 ✅ 8 luật injection (test_container)
- AC7 ✅ lifecycle idempotent + skip (test_container)
- AC8 ✅ 7 case subscribe (test_event_bus)
- AC9 ✅ sync error isolation (test_event_bus)
- AC10 ✅ async flush + caplog + sync-thread (test_event_bus)
- AC11 ✅ 6 case ValidationError (test_execution_plan)
- AC12 ✅ roundtrip equality (test_execution_plan)
- AC13 ✅ 107 pass ×2 nơi, coverage 94.82% (test riêng 5 file)
- AC14 ✅ test_import 2 dòng pin (test_import)
- AC15 ✅ overwrite + 2 thread no deadlock (test_container)
- AC16 ✅ concurrent 2×50 + unsubscribe trong handler (test_event_bus)
- AC17 ✅ check_upgrade 4 case + invariant (test_contracts)
- AC18 ✅ Event.to_dict + unicode path (test_event_bus + test_contracts)
- AC19 ✅ has/clear + singleton reset (test_container)
- AC20 ✅ parse/compare precedence (test_semver)

## Kết luận
- [x] **TẤT CẢ PASS (20/20 AC)** — sẵn sàng đánh giá cuối.
