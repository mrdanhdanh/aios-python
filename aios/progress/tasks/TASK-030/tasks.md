# TASK-030 — Tasks Breakdown

**Trạng thái**: spec v3 đã qua critique ×2 (15 + 15 vấn đề resolved) — review → implement

## Checklist

- [ ] **T1. Contracts** — `harness/execution/contracts.py`: CheckKind/Check/VerificationTask (base_dir C2-04)/CheckResult/Verdict (4)/VerificationResult + **EvidenceServices Protocol (P1-02 — duck-typed Callable/Any)** — extra=forbid
- [ ] **T2. Errors** — `errors.py`: VerificationError base
- [ ] **T3. Evidence collect** — `evidence.py`: collect_evidence (execution_ref resolution C1-01/P3-08: get_state(ref) → get_state(f"graph:{ref}") nếu chưa prefix → không thấy partial; plan.json/execution-graph.json theo namespace; runtime-events.json query_audit(10000) + filter execution_id + sort (timestamp,id) asc P3-02; truncated detection P2-01; tool-results từ state results P2-04; bỏ test-results/evaluation v1)
- [ ] **T4. Pipeline** — `pipeline.py`: run_checks (5 kinds; TEST_RUN/COVERAGE runner contract Callable[[str],tuple[bool,float]] C2-07; runner None → skipped; CUSTOM qua custom_checks dict P3-03; base_dir absolute khuyến cáo P3-05), compute_verdict (thứ tự: check FAIL > INCONCLUSIVE > PASS; skipped postcondition → INCONCLUSIVE C1-03; critical evidence P1-01; 0 postconditions → PASS_WITH_WARNING P3-04; truncation → INCONCLUSIVE P2-01)
- [ ] **T5. VerificationHarness** — `verification.py`: kế thừa Harness H1; run() → pipeline → **persist VerificationResult TRƯỚC return (C2-01: state verification= + verdict.json qua ArtifactService convention H1 — id f"harness:{run_id}:verdict", metadata kind "verdict" — P2-05)**; verify() raise khi verdict FAIL (sau persist); ctx.config["task"] (P3-06)
- [ ] **T6. Replay** — `replay.py`: round-trip integrity check (P2-03: tái tính verdict từ check_results so verdict ghi → diff tamper)
- [ ] **T7. Config + wiring** — `config.py` ExecutionSettings (collect_runtime_evidence P3-07 note), `config.yaml`, `runtime_kernel.py` (dựng VerificationHarness với services {state, events, artifacts} + registry.register)
- [ ] **T8. Unit tests** — `tests/test_harness_execution.py`: contracts, evidence (resolution namespace, critical OR, truncated, deterministic), pipeline (5 kinds, verdict 6 nhánh + INV-019 + skipped), verification harness (PASS; postcondition fail → verify raise + state verdict + verdict.json trong ArtifactService), replay (diff [] gốc; tamper → diff ≠ []), integration (e2e qua HarnessRunner + RuntimeKernel)
- [ ] **T9. Arch tests** — `test_architecture.py`: `test_inv019_verification_before_verdict` (behavioral: execution ok + postcondition fail → FAIL không PASS; skipped → INCONCLUSIVE) + AST (pipeline Verdict.FAIL literal; verification verify raise); allow-list H1 KHÔNG MOD (P1-02); rglob phủ harness/execution
- [ ] **T10. Full suite + coverage** — ≥ 45 test mới (tổng ≥ 1169), coverage hard ≥ 90% (mục tiêu 95%)
- [ ] **T11. test.md + evaluation.md** — đối chiếu 10 AC

## Bước kế tiếp
Review → implement → test → evaluate → commit
