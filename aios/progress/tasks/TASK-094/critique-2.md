# TASK-094 — Critique vòng 2

## P1 — Severity mapping có đủ Coverage không?

**Phát hiện**: Chỉ map HarnessHookError → HIGH, HarnessLifecycleError → MEDIUM. Nếu có exception mới (ReleaseGateError, MetaError, CoverageError) → default LOW → có thể understimate severity.

**Giải pháp**: Thêm mapping cho tất cả harness error subclasses hiện có:
- `ReleaseGateError` → HIGH (blocks release)
- `MetaError` → HIGH (trust violation)
- `CoverageError` → MEDIUM (readiness issue)
- `BehavioralConformanceError` → MEDIUM
- `ReadinessError` → MEDIUM
- Base `HarnessError` → LOW (unknown subclass)

## P2 — FailureRecord.evidence size?

**Phát hiện**: evidence chứa full events + report từ HarnessRunner — có thể rất lớn (hàng nghìn events). Nếu lưu nhiều records → memory bùng nổ.

**Giải pháp**: v1: evidence = {summary, error_type, error_message, status, metrics} — extract subset, KHÔNG lưu full events. Full evidence vẫn trong ArtifactService. Giữ corpus nhẹ.

## Kết luận vòng 2

P1: mở rộng severity mapping → cover tất cả error subclasses. P2: thu hẹp evidence field → chỉ extract subset. Spec → v1.2. Ready implement.
