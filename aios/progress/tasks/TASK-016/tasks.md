# TASK-016 — Tasks Breakdown (Architecture Hardening)

> Ngày: 2026-08-13 | Spec: `spec.md` (approved — critique ×2 resolved 23 vấn đề)

## Checklist

### T1 — Docs: architecture.md
- [ ] T1.1 Section "Architecture Invariants" (INV-001..010 + bảng enforce status)
- [ ] T1.2 Control Plane vs Execution Plane (sơ đồ 2 plane + text) — #1/#11
- [ ] T1.3 Dependency 1 chiều Agent→Capability→Tool→Infra — #4
- [ ] T1.4 System Knowledge = System Brain (Registries→Catalog→KG→SystemKnowledge→Orchestrator) — #9
- [ ] T1.5 Flow sửa: Evaluation post-execution observer (#5); KB vs KG (#6); Context vs Memory (#7); Scheduler/Resource/Execution 3 vai (#8)
- [ ] T1.6 Bảng tiến độ cập nhật: 490 tests, 95.96%, TASK-012 done (C2-08)

### T2 — Docs: ADR-0004 + PLAN.md
- [ ] T2.1 `docs/adr/0004-architecture-invariants.md` — 4 invariant chốt + rationale + tham chiếu 10 INV (không copy) + gap sandbox (C2-09)
- [ ] T2.2 `docs/PLAN.md`: link ADR-0004 mục Quyền hạn + ghi chú invariants + Architecture Health→M4 + ADR index 0001..0004 (C2-07)

### T3 — Helper + Architecture tests
- [ ] T3.1 `backend/tests/_arch_scan.py`: collect_imports (2 tập, resolve relative thuần, mọi Import node), assert_no_imports (dot-boundary), SRC_ROOT
- [ ] T3.2 `backend/tests/test_architecture.py` — 12 test (INV-003/004(+premise)/005(A+B)/007(call-site)/009(4 business)/010/006 purity/001-002 skip/scan detects/scan nested/resolve relative)

### T4 — Chạy test + đánh giá
- [ ] T4.1 `pytest -q` toàn bộ pass (490 + mới)
- [ ] T4.2 `evaluation.md` đối chiếu 10 AC
- [ ] T4.3 PROGRESS.md / LOG.md / STATS.md cập nhật
- [ ] T4.4 Commit + working tree sạch
