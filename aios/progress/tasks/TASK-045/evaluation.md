# TASK-045 — Evaluation

> Bổ sung hồi tố 2026-08-15 khi đóng hard gate (evaluation ban đầu ghi trong LOG.md).

## Đối chiếu acceptance criteria
1. **Đạt** — `ApiNamespace` 4 giá trị đúng PLAN (internal/public/extension/experimental).
2. **Đạt** — `check()` đúng với `^2.0` (major match), `>=1.8`, `1.8.0`, `*` (matrix test).
3. **Đạt** — thiếu runtime contract → fail với lý do rõ (fail-fast).
4. **Đạt** — `extra=forbid` cho contract model.
5. **Đạt** — import allow-list: extension/ chỉ pydantic/stdlib + semver (arch test `test_m8_extension_*`).
6. **Đạt** — test phủ matrix + namespace + errors.

## Kết luận
TASK-045 đạt phạm vi Extension Contracts (E3): 4 namespace phân biệt rõ Internal/Public/Extension/Experimental, Compatibility Matrix fail-closed bảo vệ Core khỏi plugin incompatible. Nền cho TASK-046..049.
