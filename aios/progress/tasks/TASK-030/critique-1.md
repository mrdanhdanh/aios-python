# Critique vòng 1 — TASK-030 (Execution Verification, H2)

**Critic**: subagent critic | **Ngày**: 2026-08-15 | **Spec phản biện**: v1

## Đánh giá chung
4 P1 (2 sai dữ kiện code thật) + 7 P2 + 4 P3. Mức sẵn sàng 2/5.

## P1 — Blockers
- **C1-01**: `execution_ref` không xác định namespace (plan.id vs graph:id). → **Resolution**: resolution thứ tự: (1) `get_state(ref)` → (2) `get_state(f"graph:{ref}")` → (3) prefix `graph:` tra thẳng → (4) không thấy → evidence partial + INCONCLUSIVE. Convention caller: plan.id.
- **C1-02**: `request.json`/`normalized-request.json` KHÔNG có nguồn (state chỉ lưu plan/graph; request_ref bị cắt 200; Normalizer không persist). → **Resolution (a)**: BỎ 2 file này v1, thay bằng plan.json (chứa request_ref) — lệch PLAN có chủ đích, ghi rõ.
- **C1-03**: Verdict cho check `skipped` không định nghĩa → đường false-PASS vi phạm INV-019. → **Resolution**: postcondition skipped → KHÔNG bao giờ PASS → INCONCLUSIVE (detail "check skipped"); invariant/precondition skipped → PASS_WITH_WARNING. Test: runner None + postcondition khác pass → INCONCLUSIVE.
- **C1-04**: Allow-list "mở" đã bị đóng bởi test H1 rglob (allow chỉ config/logging/state/artifacts/contracts.artifact). → **Resolution**: chốt **services injectable duck-typed (Protocol EvidenceServices)** — KHÔNG import kernel.graph/planning/observability; plan/graph json đọc qua `state.get_state(ref)["plan"|"graph"]`; events qua instance inject (thêm `kernel.services.events` vào allow-list + chứng minh audit query).

## P2 — Major
- **C2-01**: VerificationResult lưu đâu trước verify hook raise — không xác định. → **Resolution**: `run()` persist VerificationResult TRƯỚC return (state `verification=` + verdict.json qua ArtifactService); verify() chỉ raise sau khi lưu; AC: sau run FAIL state["verification"]["verdict"]=="fail" + verdict.json tồn tại.
- **C2-02**: Replay không deterministic với FS thật + timestamps diff nhiễu. → **Resolution**: replay v1 = tái lập trace (thứ tự events + plan/graph) + tái tính verdict từ `check_results` ĐÃ GHI (không chạy lại check trên FS); diff normalize (strip timestamps).
- **C2-03**: "Critical evidence" không định nghĩa. → **Resolution**: critical set v1 = {plan.json, events.json}; graph/artifacts/evaluation optional (bỏ file, không đổi verdict) — bảng nguồn → critical → verdict khi thiếu.
- **C2-04**: `checks_config` mâu thuẫn YC-1 vs §3; base_dir không nguồn. → **Resolution**: bỏ checks_config; thêm `VerificationTask.base_dir: str` (cho FILE_EXISTS/CONTAINS).
- **C2-05**: query_audit(limit=100) cắt ngầm + DESC. → **Resolution**: `query_audit(limit=10000)` + filter `payload.execution_id == resolved_ref` + sort asc theo timestamp.
- **C2-06**: INCONCLUSIVE (thiếu evidence) che FAIL chắc chắn. → **Resolution**: thứ tự verdict: **check-derived FAIL (postcondition/invariant) > INCONCLUSIVE (thiếu evidence) > PASS/PASS_WITH_WARNING**; test: postcondition fail + thiếu events → FAIL.
- **C2-07**: Coverage scope không định nghĩa. → **Resolution**: runner contract `Callable[[str], tuple[bool, float]]` (path → success, line_coverage_pct); COVERAGE: success and coverage ≥ min; TEST_RUN: success. v1 không tự chạy pytest (H3).

## P3 — Minor
- **C3-01**: Bỏ `policy_checks_enabled?` (Policy Checks → H4/H5).
- **C3-02**: `evidence_enabled` mâu thuẫn INV-018 → đổi `collect_runtime_evidence: bool` (chỉ gate collect; runner luôn tạo events/report).
- **C3-03**: Trùng tên events.json → evidence package dùng `runtime-events.json`.
- **C3-04**: Chốt ≥ 45 test mới (tổng ≥ 1169) + hard coverage ≥ 90% (mục tiêu 95%+).

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C1-01..C1-04 (P1) + C2-01..C2-07 (P2) + P3 → spec v2, rồi critique vòng 2.
