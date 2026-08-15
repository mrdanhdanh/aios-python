# TASK-064 — Critique vòng 2

> Critic vòng 2 (độc lập, sau khi resolve vòng 1). Kiểm tra spec v2.

## Các vấn đề tìm được

### C2-01 (P1) — Deprecated API detector cần input rõ
"Phát hiện usage deprecated" mơ hồ — detector nhận gì?
→ **Resolve**: Detector nhận `used: list[str]` (id contract được dùng) → nếu `used` chứa contract DEPRECATED → warning kèm tên migration_path. Unit test: `check_deprecated_usage(["plugin"])` → 1 warning; không dùng deprecated → 0 warning.

### C2-02 (P2) — Contract Runtime cần định nghĩa "schema" là gì
Runtime không phải class contract như Agent/Tool — schema_ref trỏ đâu?
→ **Resolve**: Runtime contract schema_ref = `kernel.runtime_kernel.RuntimeKernel` (class thật) + notes mô tả "Runtime Contract = 9 services + lifecycle (start/stop) + DI"; version = "1.0.0" freeze baseline.

### C2-03 (P3) — contract list cần cột status đồng bộ với check
Không đồng bộ → người dùng nhìn 2 bảng khác nhau.
→ **Resolve**: `contract list` in cột lifecycle; `contract-check` in status ✓/⚠/✗ + lý do; cả hai dùng chung nguồn ContractCatalog.

## Kết luận vòng 2
Đã resolve — **spec v2 đạt, được phép implement**.
