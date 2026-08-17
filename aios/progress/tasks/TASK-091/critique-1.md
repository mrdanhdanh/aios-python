# Critique vòng 1 — TASK-091 (M13-P2: Meta-Harness)

> Phản biện spec v1 bởi critic agent (độc lập) — 2026-08-17
> Đối chiếu code thật: `harness/execution/{pipeline,evidence,replay,contracts}.py`, `harness/contracts.py`, `harness/coverage/{coverage,readiness}.py`, `kernel/runtime_kernel.py`, `harness/runner.py`, `tests/test_harness_execution.py`, `tests/test_harness_coverage.py`.
> **Mức sẵn sàng v1: 2.5/5** — 2 P1 + 5 P2 + 3 P3. Tất cả đã RESOLVED (spec v2).

## P1 — Phải sửa

### P1-1 — BROKEN_VERIFIER semantics đảo ngược → Meta vĩnh viễn FAIL
- **Vấn đề**: Stub luôn trả PASS → detected=False → Meta luôn FAIL → AC12 exit 0 không bao giờ đạt; "bắt được" (caught) phải là thành công.
- **RESOLVED**: đảo semantics — BROKEN_VERIFIER `detected=True` khi Meta **phát hiện** stub hỏng (stub trả PASS trên evidence thiếu = vi phạm oracle → bắt được). Tách 2 khái niệm: (a) Meta bắt được verifier hỏng = thành công (fail_closed=True); (b) verifier dưới test không fail-closed = Meta FAIL. Thêm test riêng (b): monkeypatch `compute_verdict` trả PASS trên evidence thiếu → fail_closed=False → Meta FAIL — đây mới là "verify the verifier" thật.

### P1-2 — AC13 "không regression" mâu thuẫn AC14 — thiếu danh sách test cũ phải sửa
- **Vấn đề**: Cập nhật negative 6/8→8/8 phá 3 test coverage: `test_negative_6_of_8`, `test_metrics_and_summary`, `test_fail_closed_not_ready`.
- **RESOLVED**: liệt kê rõ trong spec: cập nhật 3 test (kỳ vọng mới 8/8, replay 1.0, overall 1.0, READY); `test_ready_when_replay_covered` vẫn pass (override thủ công).

## P2 — Nên sửa

### P2-1 — Oracle "độc lập" chưa được kiểm chứng — thiếu AC chống circular
- **RESOLVED**: ghi rõ engine KHÔNG gọi hàm production để tính `expected_state` (hardcode); thêm AC16: monkeypatch `compute_verdict`/`replay_verdict` trả sai → Meta phát hiện → fail_closed=False → status FAIL. Ghi nhận residual circularity (oracle cùng nguồn spec) + M16/dsh là path độc lập thật.

### P2-2 — CORRUPTED_ARTIFACT chưa rõ cơ chế check
- **RESOLVED**: tự viết sha256 check (engine thuần): content bytes + ref cố ý sai → `fail_closed = (sha256(content) != ref)`. `hashlib` đã trong allow-list (TASK-089).

### P2-3 — REPLAY_MISMATCH chưa rõ cách build evidence
- **RESOLVED**: evidence mẫu `{"verdict": "pass", "check_results": [CheckResult(passed=False)], "critical_evidence": True}` → recomputed FAIL → msg chứa "TAMPER". `fail_closed = "TAMPER" in verifier_state` (msg — Verdict enum không có TAMPER).

### P2-4 — Thiếu case "verify phase bị skip hoàn toàn"
- **RESOLVED**: thêm case 8 `VERIFY_SKIPPED`: harness `verify()` no-op → HarnessRunner COMPLETED → Meta phát hiện (run COMPLETED mà không verify → không PASS) — integration case.

### P2-5 — make_registry fixture không đồng bộ production
- **RESOLVED**: cập nhật `make_registry` thêm `MetaHarness` + `_COMPONENT_MODULES["meta"]` + test component total 7→8.

## P3 — Góp ý (đã tích hợp)

- **P3-1** `detected` lẫn lộn fail-closed vs exact match → **RESOLVED**: đổi tên `detected` → `fail_closed` (rõ nghĩa).
- **P3-2** reproducible chưa định nghĩa → **RESOLVED**: `{aios_version, python_version, registry_harness_ids}` (không timestamp/run_id).
- **P3-3** evidence module tồn tại không chứng minh meta PASS → **RESOLVED**: ghi nhận giới hạn (evidence = module tồn tại); marker mạnh hơn defer M13.2.

## Kết luận

- [x] Cần sửa trước khi implement — tất cả P1/P2/P3 đã RESOLVED → spec v2.