# TASK-092 — Tasks breakdown (checklist)

> Thực hiện trạng: spec v1.1 (tích hợp critique-1 P1 + critique-2 P1-P5). Hard gate đủ → implement.

## Implement
- [ ] T1: Tạo `harness/release/contracts.py` — `ReleaseGateStatus` + `ReleaseGateReport` (extra="forbid", không timestamp)
- [ ] T2: Tạo `harness/release/engine.py` — `ReleaseGateEngine.evaluate(readiness, meta)` pure combiner (PASS iff cả 2 PASS; else BLOCKED; summary rõ lý do)
- [ ] T3: Tạo `harness/release/errors.py` — `ReleaseGateError(HarnessError)`
- [ ] T4: Tạo `harness/release/harness.py` — `ReleaseGateHarness(Harness)` id="release"; `run()` chạy coverage+meta qua HarnessRunner (try/except → BLOCKED nếu sub fail), `verify()` strict fail-closed, `_persist`/`get_report`
- [ ] T5: Tạo `harness/release/__init__.py` — exports
- [ ] T6: Wiring `runtime_kernel.py` — `ReleaseGateHarness(coverage_harness, meta_harness, state_service=...)` → register id="release" + container
- [ ] T7: CLI `cli.py` — subparser `harness release` + `--no-strict` + dispatch + `_harness_release` handler
- [ ] T8: Coverage `_COMPONENT_MODULES["release"] = "aios_core.harness.release"`

## Test
- [ ] T9: Tạo `tests/test_harness_release.py` — 12 AC (engine pure + 2 path BLOCKED + shape + harness lifecycle + CLI + determinism)
- [ ] T10: Cập nhật 4 registry test (`test_harness_{benchmark,doctor,evaluation,testing}`) — thêm `"release"` (10 harness)
- [ ] T11: Cập nhật `test_harness_coverage.py::test_registry_has_coverage` — assert `len==10`
- [ ] T12: Chạy full suite + arch-health + doctor — 0 regression

## Docs
- [ ] T13: `evaluation.md` — đối chiếu 12 AC
- [ ] T14: `test.md` — test results thật
- [ ] T15: Cập nhật `PROGRESS.md` (TASK-092 done) + `LOG.md`
- [ ] T16: Commit TASK-092
