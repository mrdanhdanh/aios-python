# TASK-046 — Implementation checklist

- [x] Spec + critique ×2 resolve.
- [x] Review pre-implement.
- [ ] `ecosystem/contracts.py` (EntryKind, Publisher, EcosystemEntry).
- [ ] `ecosystem/errors.py`.
- [ ] `ecosystem/registry.py` (SQLite upsert + search + list).
- [ ] `ecosystem/__init__.py` (ban đầu chỉ registry + contracts).
- [ ] CLI `aiagent ecosystem search`.
- [ ] `tests/test_ecosystem_registry.py` + arch allow-list.
- [ ] Regression + progress + commit.

# Review pre-implement
**APPROVED có điều kiện**: registry thuần index/search, upsert ON CONFLICT, search 5 trường, allow-list độc lập extension.
