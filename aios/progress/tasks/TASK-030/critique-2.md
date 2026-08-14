# Critique vòng 2 — TASK-030 (Execution Verification, H2)

**Critic**: subagent critic | **Ngày**: 2026-08-15 | **Spec phản biện**: v2

## Mục A — Kiểm chứng resolution vòng 1
C1-01 ✅ · C1-02 ✅ · C1-03 ✅ · C1-04 ⚠️ MÂU THUẪN (§5.1 vẫn "quyết định mở" → P1-02) · C2-01 ⚠️ (verdict.json không trong HarnessReport.artifacts → P2-05) · C2-02 ⚠️ (replay tautology → P2-03) · C2-03 ❌ (graph runs: state không có "plan" key + executor không emit → luôn INCONCLUSIVE → P1-01) · C2-04 ✅ · C2-05 ⚠️ (cap 10000 cắt ngầm → P2-01) · C2-06 ✅ · C2-07 ✅ · C3-01..04 ✅

## Mục B — Vấn đề mới
### P1
- **P1-01**: Critical set {plan.json, runtime-events.json} — graph executions: state `graph:{id}` KHÔNG có key "plan"; executor/scheduler không emit event → runtime-events.json = [] → mọi graph verification INCONCLUSIVE.
  → **Resolution**: critical set OR theo namespace: `(plan.json ∨ execution-graph.json) ∧ runtime-events.json`; test graph run → PASS (không INCONCLUSIVE).
- **P1-02**: §5.1 "quyết định mở" mâu thuẫn C1-04.
  → **Resolution**: chốt **duck-typed thuần** — EvidenceServices Protocol (Callable/Any), evidence.py KHÔNG import kernel.events/kernel.services.events; runtime_kernel.py (ngoài harness/) là nơi duy nhất import EventService → **KHÔNG MOD _HARNESS_ALLOWED_AIOS**.

### P2
- **P2-01**: query_audit(10000) cắt ngầm không phát hiện. → **Resolution**: `if filtered_count == limit: evidence["truncated"]=True` → verdict INCONCLUSIVE (hoặc PASS_WITH_WARNING + detail).
- **P2-02**: File vắng vs rỗng chưa định nghĩa. → **Resolution**: plan-namespace cần ≥1 event khớp execution_id; graph-namespace chấp nhận [] (executor không emit — note).
- **P2-03**: Replay tautology. → **Resolution**: replay = **round-trip integrity check**: đọc verdict.json → tái tính verdict từ check_results → diff giữa verdict ghi và tái tính; test tamper (sửa verdict.json) → diff ≠ [].
- **P2-04**: Nguồn evidence 8 loại không chốt. → **Resolution**: bảng nguồn: tool-results/ = state[ref]["results"]; **bỏ test-results/ + evaluation.json v1** (không nguồn deterministic); artifacts/ = ArtifactService.list() filter metadata.
- **P2-05**: verdict.json convention. → **Resolution**: run() ghi qua ArtifactService: id `f"harness:{run_id}:verdict"`, storage_path `harness/{safe_run_id}/verdict.json`, metadata {run_id, kind:"verdict"} — get_evidence fallback tìm thấy; AC5 wording "tồn tại trong ArtifactService (query qua get_evidence/list)".

### P3
- **P3-01**: EvidenceServices Protocol đặt contracts.py + signature đầy đủ.
- **P3-02**: Sort asc tie-break (timestamp, id).
- **P3-03**: CUSTOM checks inject qua `run_checks(..., custom_checks: dict[str, Callable]|None)` theo tên.
- **P3-04**: 0 postconditions + pass → PASS_WITH_WARNING (không PASS vacuous).
- **P3-05**: base_dir khuyến cáo absolute path (test deterministic).
- **P3-06**: `ctx.config["task"]` chứa VerificationTask.
- **P3-07**: collect_runtime_evidence=False → INCONCLUSIVE hầu hết — note hệ quả.
- **P3-08**: C1-01 viết lại: (1) get_state(ref) → (2) nếu ref chưa prefix graph: → get_state(f"graph:{ref}") → (3) không thấy → partial + INCONCLUSIVE.

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve P1-01, P1-02 + P2-01..05 + P3 → spec v3. Sau vòng này **approve**.
