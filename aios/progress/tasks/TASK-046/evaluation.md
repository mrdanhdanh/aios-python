# TASK-046 — Evaluation

> Bổ sung hồi tố 2026-08-15 khi đóng hard gate (evaluation ban đầu ghi trong LOG.md).

## Đối chiếu acceptance criteria
1. **Đạt** — Entry 10 kinds, extra=forbid.
2. **Đạt** — registry index/update/remove + persist qua restart.
3. **Đạt** — search theo keyword (id/name/description) + filter kind.
4. **Đạt** — search trả sorted deterministic.
5. **Đạt** — duplicate (kind, id) → update, không lỗi.
6. **Đạt** — import allow-list: ecosystem/ chỉ pydantic/stdlib + semver + metadata (arch test `test_m8_ecosystem_*`).
7. **Đạt** — CLI `aiagent ecosystem search <query>` hoạt động.
8. **Đạt** — test index/search/filter/persist/update/remove (`tests/test_ecosystem_registry.py`).

## Kết luận
TASK-046 đạt phạm vi Ecosystem Registry (E4): registry v2 pure index/search cho 10 loại entry, persist SQLite, discovery qua CLI — nền cho DevKit/Marketplace/Certification.
