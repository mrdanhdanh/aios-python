# TASK-046 — Critique v2 (đầy đủ)

## Phản biện độc lập vòng 2
- **P1-01**: search phải match cả publisher.name và contract namespace, không chỉ id/name/description.
- **P1-02**: index_entry nhận dict hoặc `EcosystemEntry` — normalize ở boundary.
- **P2-01**: DB bảng `ecosystem_entries` với unique (kind, id); upsert ON CONFLICT.
- **P2-02**: `list_entries(kind=None)` cho admin/doctor.
- **P3-01**: CLI `ecosystem search` trả JSON list, exit 0 kể cả rỗng.

## Resolution
- ✅ search match trên 5 trường (id, name, description, publisher.id, contract_namespace).
- ✅ normalize dict → entry ở boundary.
- ✅ UNIQUE(kind,id) + upsert.
- ✅ list_entries.
- ✅ CLI JSON.
