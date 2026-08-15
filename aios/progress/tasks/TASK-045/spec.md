# TASK-045 — Extension Contracts (M8-E3)

## Mục tiêu
Bảo vệ Core: phân biệt rõ 4 API namespace (Internal/Public/Extension/Experimental) và Compatibility Matrix — plugin khai báo `requires: { capability_contract: ^2.0 }`, AIOS kiểm tra compatibility TRƯỚC khi load (không để plugin crash Runtime lúc startup).

## Phạm vi
- Package `backend/src/aios_core/extension/`: contracts.py, matrix.py, errors.py, `__init__.py`.
- `ApiNamespace` enum (internal/public/extension/experimental) + `ExtensionContract` (id, version, namespace, requires list) + `CompatibilityResult` (ok, errors, warnings).
- `CompatibilityMatrix.check(requires, runtime_versions)` — hỗ trợ constraint `^X.Y.Z`, `>=X.Y.Z`, `X.Y.Z`, `*`; fail-fast khi thiếu runtime contract.
- Không thay đổi backend contracts; chỉ tầng kiểm tra.

## Input/Output
- Input: `requires` dict (contract id → constraint), runtime contract versions map.
- Output: `CompatibilityResult` (ok + chi tiết).

## Tiêu chí chấp nhận
1. ApiNamespace 4 giá trị đúng PLAN.
2. check() đúng với `^2.0` (major match), `>=1.8`, `1.8.0`, `*`.
3. Thiếu runtime contract → fail với lý do rõ.
4. extra=forbid cho contract model.
5. Import allow-list: extension/ chỉ pydantic/stdlib + semver.
6. Test phủ matrix + namespace + errors.
