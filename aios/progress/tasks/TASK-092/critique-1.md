# TASK-092 — Critique vòng 1 (độc lập)

> Phản biện spec.md TASK-092 từ góc nhìn independent verification. Mục tiêu: tìm lỗ hổng, thiếu sót, rủi ro trước khi implement.

## P1 — Release Gate chạy sub-harness: xử lý khi sub-harness FAIL/ERROR?

**Phát hiện**: Spec §3.3 nói `run()` chạy coverage + meta qua `HarnessRunner` rồi lấy payload. NHƯNG không nói gì nếu một sub-harness raise (exception trong `run()` hoặc `verify()`). Nếu coverage harness lỗi (ví dụ registry rỗng → readiness xây không được), `runner.execute` trả report status `FAILED`/`DIAGNOSED`, payload có thể là `None` → `engine.evaluate(None, ...)` crash → release gate crash thay vì BLOCKED.

**Rủi ro**: Fail-closed bị phá — lỗi nội bộ sub-harness làm release gate crash (không ra verdict rõ ràng).

**Giải pháp (đã áp dụng vào spec §3.3 + §5 R1)**: `run()` bọc mỗi sub-harness execute trong try/except; nếu sub-harness fail → coi như score tương ứng FAIL (readiness NOT_READY / trust FAIL) → engine → BLOCKED. Release gate LUÔN ra verdict (không crash). Đây là fail-closed đúng nghĩa: bất kỳ sự cố nào → BLOCKED.

## P2 — Tách biệt "thật" hay chỉ label?

**Phát hiện**: Nếu ReleaseGate chỉ copy `readiness.status` + `meta.status` vào 1 report rồi AND → đúng về logic NHƯNG dễ thành "label ghép" (không chứng minh độc lập). Cần đảm bảo engine KHÔNG tính readiness/trust (chỉ đọc report).

**Giải pháp (đã có trong spec §1 + §3.2)**: Engine là pure combiner — nhận 2 report đã tính, AND chúng. Engine KHÔNG import `HarnessReadinessScorer`/`MetaHarnessEngine`. AC4 + AC5 unit test chứng minh 2 path BLOCKED độc lập → tách biệt thật.

## P3 — `reproducible` có timestamp không?

**Phát hiện**: TASK-091 MetaReport bị loại bỏ timestamp (P3-2). ReleaseGateReport phải nhất quán — KHÔNG có `generated_at`/`timestamp` (để so sánh determinism + reproducible).

**Giải pháp (đã có spec §3.1)**: `reproducible` chỉ `{aios_version, python_version}`, KHÔNG timestamp. `extra="forbid"` bắt buộc.

## P4 — INV-017: import concrete sub-harness class?

**Phát hiện**: Nếu `release/harness.py` import `from ..coverage.harness import CoverageHarness` → coupling nội bộ harness→harness (có thể vi phạm allow-list tùy scanner).

**Giải pháp (đã có spec §3.3 R2)**: Constructor type `Harness` ABC (không import concrete). Chỉ import contracts (`HarnessReadinessReport`, `MetaReport`) + `HarnessRunner` (public API) + `StateService` (submodule `kernel.services.state`). INV-017 compliant.

## Kết luận vòng 1

Spec đã cover P2/P3/P4. **P1 là lỗ hổng thật** (sub-harness fail → crash) — đã resolve bằng try/except → BLOCKED. Spec v1 → v1.1 (bổ sung P1 resolution vào §3.3 + §5 R1). Sẵn sàng cho vòng 2.
