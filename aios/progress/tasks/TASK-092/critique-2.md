# TASK-092 — Critique vòng 2 (độc lập, góc nhìn khác)

> Phản biện lại spec.md TASK-092 sau vòng 1. Tập trung: edge case thực thi, ngôn ngữ contract, CLI semantics, và tính nhất quán với M13 pipeline.

## P1 — Sub-harness fail → BLOCKED: payload extraction an toàn?

**Phát hiện (tiếp nối vòng 1 P1)**: Khi sub-harness fail, `runner.execute` trả `HarnessReport` với `result.payload` = `None` (vì `run()` raise trước khi return). Nếu code làm `payload["readiness"]` trên `None` → crash. Cần extract an toàn: nếu `result.payload is None` hoặc thiếu key → coi như score FAIL.

**Giải pháp (áp dụng spec §3.3)**: `run()` kiểm tra `result.payload` không None + có key cần thiết; nếu thiếu → build report tương ứng với status FAIL (readiness NOT_READY / trust FAIL) rồi vẫn qua `engine.evaluate`. Luôn ra verdict.

## P2 — CLI exit code semantics có rõ không?

**Phát hiện**: `aiagent harness release` exit 0 (PASS) / 1 (BLOCKED). Nhưng BLOCKED bao gồm nhiều nguyên nhân (readiness NOT_READY / trust FAIL / sub-harness error). CLI output JSON phải chứa `status` + `summary` chỉ rõ lý do (từ `ReleaseGateReport.summary`).

**Giải pháp (áp dụng spec §3.4 + §3.1)**: `_harness_release` in `{"release": report, "status": ...}`; `summary` trong report chỉ rõ "RELEASE BLOCKED: <reason>". Exit code duy nhất 0/1.

## P3 — Tên module/harness có nhầm với "release process" không?

**Phát hiện**: `id="release"` + CLI `aiagent harness release` có thể nhầm với quy trình release (promotion verify→master). Cần ghi chú rõ: đây là "release GATE" (cổng kiểm soát trước release), không phải quy trình release.

**Giải pháp (áp dụng spec §3.4 + PLAN)**: comment/cli help ghi rõ "Release gate — System Readiness + Harness Trust (M13-P3)". Không đổi tên (PLAN gọi "release gate").

## P4 — Cập nhật registry tests có đủ không?

**Phát hiện**: Thêm `release` harness → runtime có 10 harness. 4 test `test_harness_registry_all_m6` assert set 9 → phải thành 10. `test_registry_has_coverage` assert `len==9` → `==10`. Nếu quên → regression.

**Giải pháp (áp dụng spec §3.6)**: Liệt kê rõ 2 chỗ cần sửa. Sẽ cập nhật trong bước implement + test.

## P5 — Có phá READY (TASK-091) không?

**Phát hiện**: Thêm `release` vào runtime → coverage component có thêm 1 entry. Nếu `_COMPONENT_MODULES` thiếu `"release"` → default `'aios_core.harness'` (tồn tại) → vẫn covered. NHƯNG để chính xác, nên thêm `"release": "aios_core.harness.release"`.

**Giải pháp (áp dụng spec §3.5)**: Thêm `_COMPONENT_MODULES["release"]`. Không phá READY (component ratio vẫn 1.0).

## Kết luận vòng 2

4 điểm (P1-P4) từ vòng 1 đã resolve. Vòng 2 tìm thêm P1 (payload None safety — cùng chủ đề fail-closed), P2 (CLI summary), P3 (naming), P4 (registry tests), P5 (component map). Tất cả đã áp dụng vào spec §3.1/§3.3/§3.4/§3.5/§3.6. **Spec đạt chuẩn hard gate** — sẵn sàng implement.
