# TASK-029 — Tasks Breakdown

**Trạng thái**: spec v3 đã qua critique ×2 (15 + 21 vấn đề resolved) — sẵn sàng review → implement

## Checklist

- [ ] **T1. Contracts** — `harness/contracts.py` (leaf — pydantic/typing/datetime/enum/uuid): HarnessRunStatus (8, COMPLETED→FAILED C1-02 + CREATED→FAILED B1), HarnessRun (ended_at/error D2), HarnessEvent, HarnessResult (metrics v1 duration_ms/phase_count), **HarnessArtifact (id deterministic f"{run_id}:{kind}" — C2-02)**, HarnessReport — extra=forbid
- [ ] **T2. Errors** — `errors.py`: HarnessError + Registration/NotFound/Lifecycle/Hook
- [ ] **T3. Lifecycle** — `lifecycle.py` (thuần): TRANSITIONS + can_transition/transition/is_terminal (terminal = COMPLETED/DIAGNOSED — lưu ý COMPLETED có outgoing FAILED — ghi chú nghĩa "outcome cuối")
- [ ] **T4. Context** — `context.py`: HarnessContext (PrivateAttr _sink; **emit_event bọc try/except C2-05**; attach_sink; model_dump không chứa sink)
- [ ] **T5. Registry + Harness ABC** — `registry.py`: Harness ABC (@property @abstractmethod id/name/version — C3-04; hooks no-op), HarnessRegistry (RLock, register/get/list, duplicate → HarnessRegistrationError; cùng id khác version → error v1 note)
- [ ] **T6. Runner** — `runner.py`: execute = try (lifecycle hooks) / except catch-all (B1: FAILED từ phase hiện tại + run.error) / finally (**evidence build: collector runner-owned attach đầu execute C3-06; sanitize `[\\/:*?"<>|]` → `_` B4; _evidence_contract 9 field C2-01; ArtifactService.store UTF-8; store fail → in-memory report B1**); duplicate run_id → HarnessError (C2-03); persist model_dump JSON (B9); get_run/get_result/get_evidence ([] nếu không tồn tại B8; **restart-safe fallback ArtifactService.list B3**); ended_at cả 2 nhánh (B6); result.artifacts = harness artifact ids (B5)
- [ ] **T7. Config + wiring** — `config.py` HarnessSettings (diagnose_on_failure), `config.yaml`, `runtime_kernel.py` (resolve ArtifactService/StateService shared + registry/runner)
- [ ] **T8. Unit tests** — `tests/test_harness_kernel.py`: contracts (extra=forbid, defaults, round-trip), lifecycle (8×8 matrix, chains), context (sink, **sink raise → no crash C2-05**), registry (duplicate, abstract TypeError C3-04), runner (happy chain + evidence 2 artifact, **on_failure raise → vẫn report FAILED C1-03**, sink raise → COMPLETED, **catch-all ngoài hook → FAILED B1**, duplicate run_id, sanitize `harness:a?b` B4, determinism trừ timestamps+**ref B2**, get_evidence restart fallback B3), integration (RuntimeKernel e2e — AC6 list JSON)
- [ ] **T9. Arch tests** — `test_architecture.py`: `test_inv017_harness_import_allowlist` (**rglob loop C3-07; external top-level `collections` B7; KHÔNG kernel.events C3-05**), `test_inv017_harness_no_kernel_impl` (**rglob đệ quy C3-07**), `test_inv017_harness_no_god_object` (**import-based cho contracts leaf — C2-04 v2**), `test_inv017_harness_call_sites`, `test_inv017_harness_no_private_access`, `test_inv017_no_harness_in_kernel`, `test_inv018_runner_builds_evidence` (literal HarnessArtifact + behavioral)
- [ ] **T10. Config + wiring tests** — `test_config.py` (harness block + env override + forbid), `test_runtime_kernel.py` (resolve registry/runner + shared instances)
- [ ] **T11. Full suite + coverage** — pytest toàn bộ, coverage ≥ 80% cứng (95% mục tiêu); git diff verify additive only
- [ ] **T12. test.md + evaluation.md** — đối chiếu AC

## Bước kế tiếp
Review → implement → test → evaluate → commit
