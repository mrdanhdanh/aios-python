# TASK-064 — Critique vòng 1

> Critic (tự — độc lập quan điểm). Phản biện spec TASK-064 trước implement.

## Các vấn đề tìm được

### C1-01 (P1) — schema_ref phải import được thật, không phải chuỗi ảo
Nếu schema_ref chỉ là string "agents.base.AgentContract" mà class không tồn tại → catalog vô nghĩa.
→ **Resolve**: schema_ref = tuple `(module_path, class_name)`; test AC2 import thật từng class (importlib) — fail nếu không resolve được.

### C1-02 (P1) — Phiên bản contract phải khớp code thật
Ghi version "1.0.0" nhưng thực tế contract chưa từng version hóa (plugin manifest có `aios` range, ModelContract có contract_version?) → số liệu bịa.
→ **Resolve**: ContractDefinition thêm trường `source_version` (version thật lấy từ code: `AiOSMetadata.version`/`contract_version` nếu có; mặc định "1.0.0" = freeze baseline) + ghi chú trong notes. Không khai báo version cao hơn code.

### C1-03 (P2) — Plugin DEPRECATED phải có lý do + thời điểm
Deprecate plugin v1 mà không ghi lý do → người dùng không biết dùng gì thay thế.
→ **Resolve**: `deprecated_in` (semver) + `deprecated_reason` (bắt buộc khi lifecycle=DEPRECATED) + migration_path mô tả hướng thay thế.

### C1-04 (P2) — Matrix ⚠/✗ ngữ nghĩa rõ
✓ = compatible + không warning; ⚠ = warning (deprecated/usage cũ) nhưng không chặn; ✗ = breaking (chặn release Gate C).
→ **Resolve**: Ghi rõ ngữ nghĩa trong spec + check report có `blocking` flag (breaking → blocking=True).

### C1-05 (P3) — CLI in bảng căn lề
Matrix in CLI phải dễ đọc (padding đều, dấu phân cách).
→ **Resolve**: Format `id | version | lifecycle | status` với cột padding; ghi rõ ví dụ output trong test.

## Kết luận
P1/P2/P3 resolve vào spec v2 (C1-01: import thật; C1-02: source_version; C1-03: deprecated_reason; C1-04: blocking; C1-05: format CLI).
